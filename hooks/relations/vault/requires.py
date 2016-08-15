from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes
from charms.reactive import is_state


class VaultClient(RelationBase):
    scope = scopes.GLOBAL
    auto_accessors = ['host', 'port', 'token']

    @hook('{requires:vault}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')
        data = {
            'host': self.host(),
            'port': self.port(),
            'token': self.token(),
        }
        if all(data.values()):
            self.set_state('{relation_name}.available')

    @hook('{requires:vault}-relation-{broken,departed}')
    def broken(self):
        if(is_state('{relation_name}.available')):
            self.remove_state('{relation_name}.available')

    def get_token(self, name):
        """
        Ask Vault for a specific token

        :param str name: New token to use.
        """
        self.set_remote('token', name)
