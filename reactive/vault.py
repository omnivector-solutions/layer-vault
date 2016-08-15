import shutil
import os

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import leader_get
from charmhelpers.core.host import mkdir
from charmhelpers.core.templating import render
from charms.reactive import when, when_not, hook
from charms.reactive import set_state, remove_state

from charmhelpers.core.host import (
    service_stop,
    service_restart,
)

import charms.leadership
import hvac


@when('consul.connected')
@when_not('vault.ready')
def setup_vault(consul):
    render(
        source='config.hcl',
        target='/etc/vault/config.hcl',
        context={
            'private_address': hookenv.unit_get('private-address')
        }
    )
    service_restart('vault')
    set_state('vault.ready')


@when('vault.ready', 'leadership.is_leader')
@when_not('leadership.set.root_token')
def vault_ready():
    # client = hvac.Client()
    client = hvac.Client(url='http://localhost:8200')
    try:
        if not client.is_initialized():
            shares = 1
            threshold = 1

            result = client.initialize(shares, threshold)
            client.token = result['root_token']
            client.unseal(result['keys'][0])
            charms.leadership.leader_set(
                root_token=result['root_token'],
                key=result['keys'][0])
    except:
        hookenv.log(
            "Had a problem with Vault initialization, will try again soon")


@when('vault.token.requested', 'leadership.set.root_token')
def generate_tokens(vault):
    # client = hvac.Client()
    client = hvac.Client(url='http://localhost:8200')
    client.token = leader_get('root_token')
    for service, token in vault.requested_tokens():
        if token:
            client.create_token(
                id=token, policies=['root'], display_name=service)
        else:
            token = client.create_token(
                policies=['root'], display_name=service
                )['auth']['client_token']

        vault.provide_token(
            service=service,
            host=hookenv.unit_private_ip(),
            port=8200,
            token=token
        )


@when('leadership.set')
def unlock():
    # client = hvac.Client()
    client = hvac.Client(url='http://localhost:8200')
    if client.is_sealed():
        client.unseal(leader_get('key'))


def setup_upstart_jobs():
    hookenv.log('setting up upstart jobs')
    context = {
        'vault_path': '/usr/local/bin/vault',
        'name': 'vault',
        'vault_options': '--config=/etc/vault/config.hcl'
    }
    render('upstart.conf', '/etc/init/vault.conf', context, perms=0o644)
    service_stop('vault')


@hook('stop')
def stop():
    service_stop('vault')
    remove_state('vault.running')


@hook('install')
def install():
    hookenv.log('Installing vault')
    shutil.copyfile(
        '{}/files/vault-0.5.0'.format(hookenv.charm_dir()),
        '/tmp/vault')
    mkdir('/usr/local/bin')
    shutil.move('/tmp/vault', '/usr/local/bin/vault')
    os.chmod('/usr/local/bin/vault', 0o755)
    setup_upstart_jobs()
    hookenv.open_port(8200)
