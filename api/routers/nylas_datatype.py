from typing import List


class Grant:
    def __init__(self, id, provider, scope, grant_status, email, user_agent, ip, state, created_at, updated_at, provider_user_id, settings):
        self.id = id
        self.provider = provider
        self.scope = scope
        self.grant_status = grant_status
        self.email = email
        self.user_agent = user_agent
        self.ip = ip
        self.state = state
        self.created_at = created_at
        self.updated_at = updated_at
        self.provider_user_id = provider_user_id
        self.settings = settings

class ListResponse:
    def __init__(self, grants: List[Grant]):
        self.grants = grants
        


