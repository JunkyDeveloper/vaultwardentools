from vaultwardentools import Client

from vaultwardentools.client import Organizationuseruserdetails, UserNotFoundError


def get_organisation_users_via_mails(orga, mails: list[str], client: Client) -> list[Organizationuseruserdetails]:
    orga = client.get_organization(orga)
    org_users = client.get_users_from_organization(orga)
    users = []
    for u in org_users.values():
        if u.email in mails:
            users.append(u)
    return users


def get_organisation_user_via_mail(orga, mail: str, client: Client):
    users = get_organisation_users_via_mails(orga, [mail], client)
    if len(users) == 0:
        raise UserNotFoundError()
    return users[0]


def get_collections_list(collections):
    return list(collections["id"].values())
