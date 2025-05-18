# Tools for working with vaultwarden/bitwarden (_rs) and vaultier


This package containers a python3+ client for bitwarden which uses both a native python implementation but also wraps the official npm `@bitwarden/cli`.

The ultimate goal is certainly only to rely on python implementation against the vaultwarden/bitwarden_rs server implementation.

- [![.github/workflows/cicd.yml](https://github.com/junkydeveloper/vaultwardentools/actions/workflows/cicd.yml/badge.svg?branch=main)](https://github.com/corpusops/bitwardentools/actions/workflows/cicd.yml)

## DISCLAIMER
This library will get some updates only to bring groups working. If you find issues please report but no garantee it will be solved.
Also code contributes are wellcome!
The new maintainer is using only vaultwarden and no bitwarden, so all source code will be optimized for this solution but the goal is to be backwards compatible and support both systems!


## SECURITY CONSIDERATIONS
This library was made as a swiss-army knife, but it still a proof of concept and as such, for obvious security reasons, should not be trusted blindly even if it already appears to work pretty well.
Indeed, as the maintainers, we do not have neither the time, nor the human ressources, nor the funds to continue development and conformity specially on a password related software.
bitwardentools was designed and more oriented to manage administrative tasks via adhoc scripts around bitwarden. It was with **root/admin** privileges / **all** access in mind.

We would at least ask you to be careful, or even discourage to use it for example in a multi-user context
Specially if the users are not trusted, and the API is used on long running proccess like WEB APIS.
Or, you'll have to take the responsability of this usage and as already said on https://github.com/corpusops/bitwardentools/blob/main/USAGE.md#security-note , you should at least really take A SPECIAL++ care in the lifecycle of your consuming application to ensure that `Client.bust_cache()` is called between each different user call if this is not desired (and/or controlled), or any other cache invalidation routine will be done to ensure no leak to be possible. Also, please note that bitwardentools's cache is more a local object registry that a requests cache.
This means that misusing the library can lead to leaks where an already preloaded cache can be exploited by rogue users, so think twice to your scenarii to ensure what would one user have access with or without the cache loaded.

You should also upgrade as soon as possible to version 2.0.0 which may mitigate but not totally the situation as we can't by definition control the code consuming this library and any mis-usage, specially concerning cache invalidation calls. If you used this software in adhoc scripts, so in mono user and controlled scenarii, you still are I think still safe.

## Features
- API controllable client
- Create, Read, Update, Delete, on organizations, collection, ciphers, users (also disable/enable), and attachments
- Attach Ciphers to organization collections
- Set access at organization, collections and users levels
- Download/Upload attachments to vault and organizations
- Integrates a thin wrapper around the official npm CLI (see `call` mathod)
- Read [api](src/vaultwardentools/client.py) for more details

## Install as a python lib
```bash
pip install bitwardentools
```

## Run in dev
### Configure
```bash
cp .env.dist .env
cp .env.local.dist .env.local
printf "USER_UID=$(id -u)\nUSER_GID=$(id -g)\n">>.env
```

### Build
```bash
eval $(egrep -hv '^#|^\s*$' .env .env.local|sed  -e "s/^/export /g"| sed -e "s/=/='/" -e "s/$/'/g"|xargs)
COMPOSE_FILE="docker-compose.yml:docker-compose-build.yml" docker compose build
```

### Run

```bash
docker compose run --rm app bash
```

```bash
sed -i -e "/COMPOSE_FILE/d" .env
echo "COMPOSE_FILE=docker-compose.yml:docker-compose-dev.yml" >> .env
docker compose up -d --force-recreate
docker compose exec -u app app bash
```

### Run Tests
```bash
sed -i -e "/COMPOSE_FILE/d" .env
echo "COMPOSE_FILE=docker-compose.yml:docker-compose-dev.yml:docker-compose-test.yml" >> .env
docker compose exec -u app app tox -e linting,coverage
```

## Credits and Bibliography
- [gnunux](http://gnunux.info/) excellent articles:
    [1](http://gnunux.info/dotclear2/index.php?post/2020/10/11/%C3%89crire-un-client-Bitwarden-en-python-%3A-identifiant)
    [2](http://gnunux.info/dotclear2/index.php?post/2020/10/11/%C3%89crire-un-client-Bitwarden-en-python-%3A-cr%C3%A9er-une-organisation-et-une-collection)
    [3](http://gnunux.info/dotclear2/index.php?post/2020/10/11/%C3%89crire-un-client-Bitwarden-en-python)
- https://github.com/dani-garcia/vaultwarden/ (old: https://github.com/dani-garcia/bitwarden_rs/ )
- https://github.com/doy/rbw/tree/master/src
- https://github.com/bitwarden/jslib
- https://github.com/birlorg/bitwarden-cli/tree/trunk/python/bitwarden
- https://github.com/jcs/rubywarden


## Docs
See [USAGE](./USAGE.md) (or read below on pypi)
