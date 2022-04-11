import logging
import os

import requests


def post_github_graphql_commits(input):
    # query = """query{
    #         repository(owner: "lee-dohm", name: "octicons-ex") {
    #             object(expression: "v0.5.0") {
    #             ... on Commit {
    #                 oid
    #                 messageHeadline
    #                 committedDate
    #                 author {
    #                 user {
    #                     id
    #                     databaseId
    #                     email
    #                     login
    #                     publicKeys(first: 10) {
    #                         edges {
    #                             node {
    #                             id
    #                             key
    #                             }
    #                         }
    #                     }
    #             }
    #                 }
    #             }
    #             }
    #         }
    #     }"""
    
    query = """{
        search(query: \"rebase-network/rostra-app\", type: REPOSITORY, last: 50) {
            nodes {
            ... on Repository {
                name
                defaultBranchRef {
                name
                target {
                    ... on Commit {
                    history(first: 50, since: "2020-10-11T00:00:00") {
                        totalCount
                        nodes {
                        ... on Commit {
                            committedDate
                            message
                            messageBody
                            additions
                            author {
                            name
                            email
                            user {
                                id
                                databaseId
                                email
                                login
                                publicKeys(first: 10) {
                                edges {
                                    node {
                                    id
                                    key
                                    }
                                }
                                }
                            }
                            }
                        }
                        }
                    }
                    }
                }
                }
            }
            }
        }
        }"""


    headers = {'Content-Type': 'application/json', 'Authorization': 'bearer ' + str(os.environ.get("GITHUB_GRAPHQL_APIKEY"))}
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json(), 0
    else:
        logging.error("Query failed to run by returning code of {}. {}\n{}".format(request.status_code, request.reason, query))
        return None, -1
