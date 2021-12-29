import os, time
from flask import Flask, render_template, redirect, url_for
import markdown, frontmatter

app = Flask(__name__)

posts = []

for filename in os.listdir("posts"):
  filedata = frontmatter.load(f"posts/{filename}")

  post = {
    "title": filedata["title"],
    "date": filedata["date"],
    "content": markdown.markdown(text=filedata.content, output_format="html5", tab_length=2, extensions=["markdown.extensions.extra"])
  }

  posts.append(post)

@app.route("/post/<title>")
def post(title):
  for post in posts:
    if post["title"] == title:
      return render_template("post.html", post=post)

  return redirect(url_for("blog"))

@app.route("/")
def blog():
  return render_template("blog.html", posts=posts)

if __name__ == "__main__":
  app.run()