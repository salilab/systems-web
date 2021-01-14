#!/usr/bin/python3

"""
Update metadata stored on the local disk, used by the systems page,
by querying GitHub and PubMed.

This can be done manually (e.g. when a new system is added) or from
a crontab.

To use, make a file config.json in the same directory as this script, readable
only by the user, of the format:

{
 "github": {"username": "XXX"
            "password": "XXX"},
 "sql": {"passwd": "XXX", "host": "XXX",
         "db": "XXX", "user": "XXX"},
 "system_top": "XXX"
}

where "github" gives the username and password for access to the GitHub API;
"sql" contains connection parameters to the MySQL database with systems
information; and "system_top" is the filesystem location where the metadata
will be stored.
"""

import urllib.request
import base64
import json
import os
import re
import MySQLdb
import yaml


class GitHubRepo(object):
    def __init__(self, repo, auth):
        self.auth = auth
        m = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo)
        if not m:
            raise ValueError("Could not parse repo %s" % repo)
        self.owner = m.group(1)
        self.repo = m.group(2)
        # Note: this assumes that the main branch is the default
        self.url_root = 'https://github.com/%s/%s/tree/main/' \
                        % (self.owner, self.repo)
        self.api_root = 'https://api.github.com/repos/%s/%s' \
                        % (self.owner, self.repo)

    def get_default_headers(self):
        """Get headers needed for every API request"""
        auth = self.auth['username'] + ":" + self.auth['password']
        headers = {'Authorization':
                   'Basic %s' % base64.b64encode(auth.encode())}
        return headers

    def get_readme(self):
        def make_url_absolute(m):
            url = m.group(1)
            if not url.startswith('//') and ':' not in url:
                return '<a href="%s%s">' % (self.url_root, url)
            else:
                return m.group(0)
        headers = self.get_default_headers()
        headers['Accept'] = 'application/vnd.github.VERSION.html'
        try:
            req = urllib.request.Request(self.api_root + '/readme',
                                         None, headers)
            response = urllib.request.urlopen(req)
            urls_fixed = re.subn('<a href="([^"]+)">', make_url_absolute,
                                 response.read().decode('utf-8'))
            return urls_fixed[0]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return ''
            else:
                raise

    def get_last_commit_time(self, last_modified):
        """Get the time of the last commit, or None if there has been none
           since last time."""
        headers = self.get_default_headers()
        headers['If-Modified-Since'] = last_modified
        req = urllib.request.Request(self.api_root + '/commits/HEAD',
                                     None, headers)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return None
            else:
                raise
        return response.info()['Last-Modified']

    def get_info(self, last_modified):
        """Get repository info.
           Return JSON and the last-modified time, or None,None if the
           info hasn't changed since last time."""
        headers = self.get_default_headers()
        if last_modified:
            headers['If-Modified-Since'] = last_modified
        req = urllib.request.Request(self.api_root, None, headers)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                if last_modified:
                    # There may have been a more recent push even though the
                    # repository metadata was not updated; if so, return
                    # metadata and use the commit time as last-modified
                    last_commit = self.get_last_commit_time(last_modified)
                    if last_commit is not None:
                        resp, last_update = self.get_info(None)
                        return resp, last_commit
                return None, None
            else:
                raise
        return response.read(), response.info()['Last-Modified']

    def get_file(self, filename, binary=False):
        headers = self.get_default_headers()
        req = urllib.request.Request(self.api_root + '/contents/' + filename,
                                     None, headers)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            else:
                raise
        contents = json.load(response)
        if contents['encoding'] == 'base64':
            contents = base64.b64decode(contents['content'])
            if not binary:
                contents = contents.decode()
            return contents
        else:
            raise ValueError("Unknown encoding: %s" % contents['encoding'])


class FileUpdater(object):
    def __init__(self, root, auth):
        self.root, self.auth = root, auth

    def get_timestamp(self, fname):
        try:
            return json.load(open(fname))['Last-Modified']
        except IOError:
            return None

    def write_file(self, fname, contents, binary=False):
        if not os.path.exists(os.path.dirname(fname)):
            os.mkdir(os.path.dirname(fname))
        with open(fname, 'wb' if binary else 'w') as fh:
            fh.write(contents)

    def get_filename(self, name, filename):
        return os.path.join(self.root, name, filename)

    def update(self, name, repo):
        g = GitHubRepo(repo, self.auth)
        g_json = self.get_filename(name, 'github.json')
        last_modified = self.get_timestamp(g_json)

        info, new_last_modified = g.get_info(last_modified)
        if not info:
            # Skip update if the repo hasn't changed. This should help us to
            # avoid hitting GitHub's rate limits.
            return
        info = json.loads(info)
        info['Last-Modified'] = new_last_modified

        self.write_file(g_json, json.dumps(info))
        self.write_file(self.get_filename(name, 'readme.html'), g.get_readme())
        for f, binary in (('metadata.yaml', False), ('thumb.png', True)):
            fname = self.get_filename(name, f)
            contents = g.get_file('metadata/' + f, binary)
            if contents is not None:
                if f == 'metadata.yaml':
                    self.update_metadata(name, contents)
                self.write_file(fname, contents, binary)

    def update_metadata(self, name, contents):
        meta = yaml.load(contents)
        if 'pmid' in meta:
            url = ('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
                   '?db=pubmed&retmode=json&rettype=abstract&id=%s'
                   % str(meta['pmid']))
            response = urllib.request.urlopen(url).read()
            # Make sure it is valid JSON:
            j = json.loads(response)
            fname = self.get_filename(name, 'pubmed.json')
            self.write_file(fname, json.dumps(j))


class DatabaseConnection(object):
    def __init__(self, sql):
        self.conn = self.connect_mysql(sql)

    def connect_mysql(self, sql):
        return MySQLdb.connect(**sql)

    def get_systems(self):
        c = MySQLdb.cursors.DictCursor(self.conn)
        c.execute('SELECT name, repo FROM sys_name')
        return c


def read_config():
    """Read configuration from same directory as script"""
    fname = os.path.join(os.path.dirname(__file__), "config.json")
    with open(fname) as fh:
        return json.load(fh)


def main():
    config = read_config()
    u = FileUpdater(root=config['system_top'], auth=config['github'])
    d = DatabaseConnection(config['sql'])
    for s in d.get_systems():
        u.update(name=s['name'], repo=s['repo'])


if __name__ == '__main__':
    main()
