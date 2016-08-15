from charmhelpers.core import hookenv
from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes


class VaultClient(RelationBase):
    scope = scopes.SERVICE

    @hook('{provides:vault}-relation-{joined,changed}')
    def changed(self):
        service = hookenv.remote_service_name()
        conversation = self.conversation()

        if self.previous_token(service) != self.requested_token(service):
            conversation.set_state('{relation_name}.token.requested')

    # @not_unless('{provides:vault}.token.requested')
    def provide_token(self, service, host, port, token):
        """
        Provide a token to a requesting service.
        :param str service: The service which requested the token, as
            returned by :meth:`~provides.Vault.requested_tokens`.
        :param str host: The host where Vault can be reached (e.g.,
            the charm's private or public-address).
        :param int port: The port where Vault can be reached.
        :param str token: The token being provided.
        """
        conversation = self.conversation(scope=service)
        conversation.set_remote(
            host=host,
            port=port,
            token=token,
        )
        conversation.set_local('token', token)
        conversation.remove_state('{relation_name}.token.requested')

    def requested_tokens(self):
        """
        Return a list of tuples mapping a service name to the token
        requested by that service.  If a given service has not requested a
        specific token, an empty string is returned, indicating that
        the token should be generated.
        Example usage::
            for service, token in vault.requested_tokens():
                token = token or generate_token(service)
                vault.provide_token(**create_token(token))
        """
        for conversation in self.conversations():
            service = conversation.scope
            token = self.requested_token(service)
            yield service, token

    def requested_token(self, service):
        """
        Return the token requested by the given service.  If the given
        service has not requested a specific token, an empty string is
        returned, indicating that the token should be generated.
        """
        return self.conversation(scope=service).get_remote('token', '')

    def previous_token(self, service):
        """
        Return the token previously requested, if different from the currently
        requested token.
        """
        return self.conversation(scope=service).get_local('token')
