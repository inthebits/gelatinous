"""
Account

The Account represents the game "account" and each login has only one
Account object. An Account is what chats on default channels but has no
other in-game-world existence. Rather the Account puppets Objects (such
as Characters) in order to actually participate in the game world.


Guest

Guest accounts are simple low-level accounts that are created/deleted
on the fly and allows users to test the game without the commitment
of a full registration. Guest accounts are deactivated by default; to
activate them, add the following line to your settings file:

    GUEST_ENABLED = True

You will also need to modify the connection screen to reflect the
possibility to connect with a guest account. The setting file accepts
several more options for customizing the Guest account system.

"""

from evennia.accounts.accounts import DefaultAccount, DefaultGuest


class Account(DefaultAccount):
    """
    An Account is the actual OOC player entity. It doesn't exist in the game,
    but puppets characters.

    This is the base Typeclass for all Accounts. Accounts represent
    the person playing the game and tracks account info, password
    etc. They are OOC entities without presence in-game. An Account
    can connect to a Character Object in order to "enter" the
    game.

    Account Typeclass API:

    * Available properties (only available on initiated typeclass objects)

     - key (string) - name of account
     - name (string)- wrapper for user.username
     - aliases (list of strings) - aliases to the object. Will be saved to
            database as AliasDB entries but returned as strings.
     - dbref (int, read-only) - unique #id-number. Also "id" can be used.
     - date_created (string) - time stamp of object creation
     - permissions (list of strings) - list of permission strings
     - user (User, read-only) - django User authorization object
     - obj (Object) - game object controlled by account. 'character' can also
                     be used.
     - is_superuser (bool, read-only) - if the connected user is a superuser

    * Handlers

     - locks - lock-handler: use locks.add() to add new lock strings
     - db - attribute-handler: store/retrieve database attributes on this
                              self.db.myattr=val, val=self.db.myattr
     - ndb - non-persistent attribute handler: same as db but does not
                                  create a database entry when storing data
     - scripts - script-handler. Add new scripts to object with scripts.add()
     - cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     - nicks - nick-handler. New nicks with nicks.add().
     - sessions - session-handler. Use session.get() to see all sessions connected, if any
     - options - option-handler. Defaults are taken from settings.OPTIONS_ACCOUNT_DEFAULT
     - characters - handler for listing the account's playable characters

    * Helper methods (check autodocs for full updated listing)

     - msg(text=None, from_obj=None, session=None, options=None, **kwargs)
     - execute_cmd(raw_string)
     - search(searchdata, return_puppet=False, search_object=False, typeclass=None,
                      nofound_string=None, multimatch_string=None, use_nicks=True,
                      quiet=False, **kwargs)
     - is_typeclass(typeclass, exact=False)
     - swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     - access(accessing_obj, access_type='read', default=False, no_superuser_bypass=False, **kwargs)
     - check_permstring(permstring)
     - get_cmdsets(caller, current, **kwargs)
     - get_cmdset_providers()
     - uses_screenreader(session=None)
     - get_display_name(looker, **kwargs)
     - get_extra_display_name_info(looker, **kwargs)
     - disconnect_session_from_account()
     - puppet_object(session, obj)
     - unpuppet_object(session)
     - unpuppet_all()
     - get_puppet(session)
     - get_all_puppets()
     - is_banned(**kwargs)
     - get_username_validators(validator_config=settings.AUTH_USERNAME_VALIDATORS)
     - authenticate(username, password, ip="", **kwargs)
     - normalize_username(username)
     - validate_username(username)
     - validate_password(password, account=None)
     - set_password(password, **kwargs)
     - get_character_slots()
     - get_available_character_slots()
     - create_character(*args, **kwargs)
     - create(*args, **kwargs)
     - delete(*args, **kwargs)
     - channel_msg(message, channel, senders=None, **kwargs)
     - idle_time()
     - connection_time()

    * Hook methods

     basetype_setup()
     at_account_creation()

     > note that the following hooks are also found on Objects and are
       usually handled on the character level:

     - at_init()
     - at_first_save()
     - at_access()
     - at_cmdset_get(**kwargs)
     - at_password_change(**kwargs)
     - at_first_login()
     - at_pre_login()
     - at_post_login(session=None)
     - at_failed_login(session, **kwargs)
     - at_disconnect(reason=None, **kwargs)
     - at_post_disconnect(**kwargs)
     - at_message_receive()
     - at_message_send()
     - at_server_reload()
     - at_server_shutdown()
     - at_look(target=None, session=None, **kwargs)
     - at_post_create_character(character, **kwargs)
     - at_post_add_character(char)
     - at_post_remove_character(char)
     - at_pre_channel_msg(message, channel, senders=None, **kwargs)
     - at_post_chnnel_msg(message, channel, senders=None, **kwargs)

    """

    def at_post_login(self, session=None, **kwargs):
        """
        Called after successful login, handles character detection and auto-puppeting.
        
        We override the default entirely because we have custom logic for:
        - Auto-puppeting single characters
        - Starting character creation for new accounts
        - Handling archived characters
        """
        # IMPORTANT: Due to testing/development, there may be legacy characters
        # with inconsistent states. We need to be defensive here.
        
        from evennia.comms.models import ChannelDB
        
        # Debug logging
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
        except:
            splattercast = None
        
        # Use Evennia's get_all_puppets() method - this is the authoritative source
        all_puppets = self.get_all_puppets()
        
        if splattercast:
            splattercast.msg(f"AT_POST_LOGIN: Account {self.key} - get_all_puppets returned {len(all_puppets)} characters")
            if all_puppets:
                splattercast.msg(f"AT_POST_LOGIN: Puppets: {[(c.key, c.id) for c in all_puppets]}")
        
        # Filter for active (non-archived) characters
        # Be defensive: only treat explicitly archived=True as archived
        active_chars = []
        for char in all_puppets:
            archived_status = getattr(char.db, 'archived', False)
            if splattercast:
                splattercast.msg(f"AT_POST_LOGIN: Checking char {char.key} (#{char.id}) - archived={archived_status}")
            
            # Only exclude if explicitly archived
            if archived_status is not True:
                active_chars.append(char)
        
        if splattercast:
            splattercast.msg(f"AT_POST_LOGIN: active_chars after filtering={len(active_chars)}")
            if active_chars:
                splattercast.msg(f"AT_POST_LOGIN: Active characters: {[(c.key, c.id) for c in active_chars]}")
        
        # CRITICAL: Only start character creation if there are ZERO active characters
        if len(active_chars) == 0:
            # No active characters - start character creation
            if splattercast:
                splattercast.msg(f"AT_POST_LOGIN: No active characters, starting character creation")
            
            # Import here to avoid circular imports
            try:
                from commands.charcreate import start_character_creation
                start_character_creation(self, is_respawn=False)
            except ImportError as e:
                # Graceful fallback if charcreate not available yet
                if splattercast:
                    splattercast.msg(f"AT_POST_LOGIN_ERROR: Could not import charcreate: {e}")
                self.msg("|rCharacter creation system not available. Please contact an admin.|n")
        elif len(active_chars) == 1:
            # Exactly one active character - auto-puppet for convenience
            if splattercast:
                splattercast.msg(f"AT_POST_LOGIN: One active character, auto-puppeting {active_chars[0].key}")
            
            if session:
                self.puppet_object(session, active_chars[0])
        else:
            # Multiple active characters - let user choose with 'ic <name>'
            if splattercast:
                splattercast.msg(f"AT_POST_LOGIN: Multiple active characters ({len(active_chars)}), user must choose with 'ic <name>'")
        else:
            # Multiple active characters - let OOC menu handle selection
            if splattercast:
                splattercast.msg(f"AT_POST_LOGIN: {len(active_chars)} active characters, using OOC menu for selection")
            
            # The default Evennia behavior will show the OOC menu with 'ic <name>' option
            # This is the correct behavior for accounts with multiple characters
            pass

    pass


class Guest(DefaultGuest):
    """
    This class is used for guest logins. Unlike Accounts, Guests and their
    characters are deleted after disconnection.
    """

    pass
