from datetime import datetime
# import git


def now():

    return datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")


def today():

    return datetime.now().strftime("%Y-%m-%d")


def log(msg="", name=""):

    print("[{}] [{}] {}".format(now(), name, msg))


# def git_report():
#
#     repo = git.Repo()
#     sha = repo.head.object.hexsha
#     dirty = repo.is_dirty()
#     log('Commit: {}'.format(sha), "GitReport")
#     log('Dirty repo: {}'.format(dirty), "GitReport")

