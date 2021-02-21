# Copyright 2018 Google LLC
# Copyright 2020 Juha Autero <jautero@iki.fi>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, request, redirect
import hashlib, yaml, github
from datetime import datetime

try:
  import googleclouddebugger
  googleclouddebugger.enable()
except ImportError:
  pass

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

class CommentHandler:
    required_fields=['redirect','post_id','comment-site','message','name','email']
    optional_fields=['url']
    data_fields=['post_id','name','message']
    def __init__(self,form=None,config=None):
        if config:
            self.config=yaml.load(config,Loader=yaml.FullLoader)
        else:
            self.config={}
        if not form:
            form=request.form
        self.form=form
        self.data={}

    def validate_keys(self):
        form_keys = self.form.keys()
        for key in self.required_fields:
            if key not in form_keys:
                app.logger.warning("Required field %s missing",key)
                return False
        allowed_keys = self.required_fields + self.optional_fields
        for key in form_keys:
            if key not in allowed_keys:
                app.logger.warning("Unexpected field %s",key)
                return False
        if "siteurl" in self.config.keys():
            if self.form["comment-site"] != self.config["siteurl"]:
                app.logger.warning("site url '%s' doesn't match configuration '%s'",
                    self.form["comment-site"], self.config["siteurl"])
                return False
        return True 

    def get_id(self):
        hash = hashlib.sha256()
        for key in self.data_fields + ['date']:
            hash.update(str(self.data[key]).encode('utf-8'))
        return hash.hexdigest()

    def get_gravatar(self,email):
        hash = hashlib.md5()
        hash.update(email.strip().lower().encode('utf-8'))
        return hash.hexdigest()

    def get_redirect_url(self):
        return self.form.get('redirect')

    def set_data(self):
        for key in self.data_fields:
            self.data[key]=self.form[key]
        for key in self.optional_fields:
            if self.form.get(key):
                self.data[key]=self.form[key]
        self.data['date']= datetime.now()
        self.data['id']=self.get_id()
        self.data['gravatar']=self.get_gravatar(self.form['email'])

    def create_pull(self):
        g = github.Github(self.config["token"])
        repo = g.get_repo(self.config["repo"])
        slug=self.form['post_id']
        name=self.form['name']
        commentid = self.data['id']
        branchname = f"comment-{commentid}"
        sb = repo.get_branch(self.config['mainbranch'])
        repo.create_git_ref(ref='refs/heads/' + branchname, sha=sb.commit.sha)
        committer = github.InputGitAuthor(name,self.form['email'])
        filename = f"_data/comments/{slug}/{commentid}.yml"
        title=f"Comment {commentid} from {name} to {slug}"
        repo.create_file(filename,title,
            yaml.dump(self.data),branchname,committer)
        repo.create_pull(title=title,body="",head=branchname,base=self.config['mainbranch'])
        


@app.route('/comment',methods=['POST'])
def comment():
    handler=CommentHandler(request.form,open("config.yaml"))
    if handler.get_redirect_url():
        if handler.validate_keys():
            handler.set_data()
            handler.create_pull()
        return redirect(handler.get_redirect_url())
    else:
        abort(404)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
