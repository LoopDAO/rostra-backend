import os

from bson.objectid import ObjectId
from github import Github

from models import GithubCommit, GithubPeopel


#https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=get_commits#github.Repository.Repository.get_commits
def get_github_repo_commits(repo_name, page=1, per_page=50):
    gh = Github(base_url="https://api.github.com", login_or_token=str(os.environ.get("GITHUB_GRAPHQL_APIKEY")))
    repo = gh.get_repo(repo_name)
    #repo = gh.get_repo("rebase-network/rostra-backend")
    results = []
    commits = repo.get_commits()
    for index in range((page - 1) * per_page, min(commits.totalCount, page * per_page)):
        commit = commits[index]
        results.append(
            GithubCommit(message=commit.commit.message,
                         sha=commit.sha,
                         author=commit.commit.author.name,
                         email=commit.commit.author.email,
                         date=commit.commit.author.date.timestamp()))
    return results

#https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=get_stargazers_with_dates#github.Repository.Repository.get_stargazers_with_dates
def get_github_repo_stars(repo_name, page=1, per_page=10):
    gh = Github(base_url="https://api.github.com", login_or_token=str(os.environ.get("GITHUB_GRAPHQL_APIKEY")))
    repo = gh.get_repo(repo_name)

    stargazers = repo.get_stargazers_with_dates()
    peoples = []
    if (page > 0):
        for index in range((page - 1) * per_page, min(page * per_page, repo.stargazers_count)):
            people = stargazers[index]
            peoples.append(
                GithubPeopel(name=people.user.name,
                             login=people.user.login,
                             email=people.user.email,
                             starred_at=people.starred_at.timestamp(),
                             node_id=people.user.node_id,
                             user_id=people.user.id
                             #PublicKey=people.user.public_key
                             ))

    results = {"total_stars": repo.stargazers_count, "who_starred": peoples}

    return results
