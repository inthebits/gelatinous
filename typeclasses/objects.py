"""
Object

The Object is the class for general items in the game world.

Use the ObjectParent class to implement common features for *all* entities
with a location in the game world (like Characters, Rooms, Exits).

"""

from evennia.objects.objects import DefaultObject
from evennia.utils import gametime
import random


class ObjectParent:
    """
    This is a mixin that can be used to override *all* entities inheriting at
    some distance from DefaultObject (Objects, Exits, Characters and Rooms).

    Just add any method that exists on `DefaultObject` to this class. If one
    of the derived classes has itself defined that same hook already, that will
    take precedence.

    """


class Object(ObjectParent, DefaultObject):
    """
    This is the root Object typeclass, representing all entities that
    have an actual presence in-game. DefaultObjects generally have a
    location. They can also be manipulated and looked at. Game
    entities you define should inherit from DefaultObject at some distance.

    It is recommended to create children of this class using the
    `evennia.create_object()` function rather than to initialize the class
    directly - this will both set things up and efficiently save the object
    without `obj.save()` having to be called explicitly.

    Note: Check the autodocs for complete class members, this may not always
    be up-to date.

    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation

     account (Account) - controlling account (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       account above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     has_account (bool, read-only)- will only return *connected* accounts
     contents (list, read only) - returns all objects inside this object
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser
     is_connected (bool, read-only) - True if this object is associated with
                            an Account with any connected sessions.
     has_account (bool, read-only) - True is this object has an associated account.
     is_superuser (bool, read-only): True if this object has an account and that
                        account is a superuser.

    * Handlers available

     aliases - alias-handler: use aliases.add/remove/get() to use.
     permissions - permission-handler: use permissions.add/remove() to
                   add/remove new perms.
     locks - lock-handler: use locks.add() to add new lock strings
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()
     attributes - attribute-handler. Use attributes.add/remove/get.
     db - attribute-handler: Shortcut for attribute-handler. Store/retrieve
            database attributes using self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
            a database entry when storing data

    * Helper methods (see src.objects.objects.py for full headers)

     get_search_query_replacement(searchdata, **kwargs)
     get_search_direct_match(searchdata, **kwargs)
     get_search_candidates(searchdata, **kwargs)
     get_search_result(searchdata, attribute_name=None, typeclass=None,
                       candidates=None, exact=False, use_dbref=None, tags=None, **kwargs)
     get_stacked_result(results, **kwargs)
     handle_search_results(searchdata, results, **kwargs)
     search(searchdata, global_search=False, use_nicks=True, typeclass=None,
            location=None, attribute_name=None, quiet=False, exact=False,
            candidates=None, use_locks=True, nofound_string=None,
            multimatch_string=None, use_dbref=None, tags=None, stacked=0)
     search_account(searchdata, quiet=False)
     execute_cmd(raw_string, session=None, **kwargs))
     msg(text=None, from_obj=None, session=None, options=None, **kwargs)
     for_contents(func, exclude=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, mapping=None,
                  raise_funcparse_errors=False, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     clear_contents()
     create(key, account, caller, method, **kwargs)
     copy(new_key=None)
     at_object_post_copy(new_obj, **kwargs)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False,
            no_superuser_bypass=False, **kwargs)
     filter_visible(obj_list, looker, **kwargs)
     get_default_lockstring()
     get_cmdsets(caller, current, **kwargs)
     check_permstring(permstring)
     get_cmdset_providers()
     get_display_name(looker=None, **kwargs)
     get_extra_display_name_info(looker=None, **kwargs)
     get_numbered_name(count, looker, **kwargs)
     get_display_header(looker, **kwargs)
     get_display_desc(looker, **kwargs)
     get_display_exits(looker, **kwargs)
     get_display_characters(looker, **kwargs)
     get_display_things(looker, **kwargs)
     get_display_footer(looker, **kwargs)
     format_appearance(appearance, looker, **kwargs)
     return_apperance(looker, **kwargs)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_first_save()
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(account)- (account-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (account-controlled objects only) called just
                            after completing connection account<->object
     at_pre_unpuppet()    - (account-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(account) - (account-controlled objects only) called just
                            after disconnecting account<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_pre_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_post_move(source_location)          - always called after a move has
                        been successfully performed.
     at_pre_object_leave(leaving_object, destination, **kwargs)
     at_object_leave(obj, target_location, move_type="move", **kwargs)
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_pre_object_receive(obj, source_location)
     at_object_receive(obj, source_location, move_type="move", **kwargs) - called when this object receives
                        another object
     at_post_move(source_location, move_type="move", **kwargs)

     at_traverse(traversing_object, target_location, **kwargs) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_post_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(looker) - describes this object. Used by "look"
                                 command by default
     at_desc(looker=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_pre_get(getter, **kwargs)
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_pre_give(giver, getter, **kwargs)
     at_give(giver, getter, **kwargs)
     at_pre_drop(dropper, **kwargs)
     at_drop(dropper, **kwargs)          - called when this object has been dropped.
     at_pre_say(speaker, message, **kwargs)
     at_say(message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs)

     at_look(target, **kwargs)
     at_desc(looker=None)

    """

    pass


class GraffitiObject(Object):
    """
    Graffiti storage object for rooms.
    Stores up to 7 graffiti entries with FIFO management.
    """
    
    def at_object_creation(self):
        """Initialize graffiti storage."""
        super().at_object_creation()
        
        # Set up graffiti storage
        self.db.graffiti_entries = []  # List of graffiti entries
        self.db.max_entries = 7       # Maximum entries before cannibalization
        
        # Set basic properties
        self.key = "graffiti"
        self.db.desc = "The walls are clean."
        
        # Make it non-takeable and locked in place
        self.locks.add("get:false()")
        self.locks.add("drop:false()")
        
        # Add aliases for examination
        self.aliases.add(["tags", "writing", "wall", "walls"])
        
        # Set @integrate attribute for room integration
        self.db.integrate = True
        self.db.integration_priority = 3  # Lower priority than flying objects
        self.db.integration_desc = "The walls have been daubed with colorful graffiti."
        
    def add_graffiti(self, message, color, author=None):
        """
        Add a graffiti entry to the storage.
        
        Args:
            message (str): The graffiti message
            color (str): ANSI color code
            author (Object, optional): Who created the graffiti
            
        Returns:
            str: The formatted graffiti entry that was added
        """
        if not self.db.graffiti_entries:
            self.db.graffiti_entries = []
            
        # Format the entry - separate color code from display text
        color_start = f"|{color}"
        color_end = "|n"
        formatted_entry = f"Scrawled in {color_start}{color}{color_end} paint: {color_start}{message}{color_end}"
        
        # Add to storage
        self.db.graffiti_entries.append({
            'entry': formatted_entry,
            'message': message,
            'color': color,
            'author': author.key if author else 'someone',
            'timestamp': str(gametime.gametime())
        })
        
        # Enforce FIFO limit (cannibalization)
        if len(self.db.graffiti_entries) > self.db.max_entries:
            self.db.graffiti_entries.pop(0)  # Remove oldest entry
            
        # Update description and integration
        self._update_description()
        return formatted_entry
    
    def remove_random_characters(self, amount=10):
        """
        Remove random characters from random graffiti entries (solvent effect).
        
        Args:
            amount (int): Approximate number of characters to remove
            
        Returns:
            int: Actual number of characters removed
        """
        if not self.db.graffiti_entries:
            return 0
            
        removed_count = 0
        entries_to_remove = []
        
        # Randomly remove characters from random messages
        for _ in range(amount):
            if not self.db.graffiti_entries:
                break
                
            # Pick a random entry
            entry_index = random.randint(0, len(self.db.graffiti_entries) - 1)
            entry = self.db.graffiti_entries[entry_index]
            
            # Remove a random character from the message
            message = entry['message']
            if len(message) > 0:
                char_index = random.randint(0, len(message) - 1)
                new_message = message[:char_index] + message[char_index + 1:]
                entry['message'] = new_message
                
                # Update the formatted entry
                color_start = f"|{entry['color']}"
                color_end = "|n"
                entry['entry'] = f"Scrawled in {color_start}{entry['color']}{color_end} paint: {color_start}{new_message}{color_end}"
                removed_count += 1
                
                # Mark empty entries for removal
                if len(new_message.strip()) == 0:
                    entries_to_remove.append(entry_index)
        
        # Remove empty entries (in reverse order to maintain indices)
        for index in sorted(entries_to_remove, reverse=True):
            if index < len(self.db.graffiti_entries):
                self.db.graffiti_entries.pop(index)
        
        self._update_description()
        return removed_count
    
    def clear_all_graffiti(self):
        """Remove all graffiti entries and delete the object."""
        self.db.graffiti_entries = []
        self.delete()
        
    def has_graffiti(self):
        """
        Check if there are any graffiti entries.
        
        Returns:
            bool: True if graffiti exists
        """
        return bool(self.db.graffiti_entries)
    
    def get_total_characters(self):
        """
        Get total character count across all graffiti entries.
        
        Returns:
            int: Total character count
        """
        if not self.db.graffiti_entries:
            return 0
        return sum(len(entry['message']) for entry in self.db.graffiti_entries)
    
    def _update_description(self):
        """Update the object's description based on current graffiti."""
        if not self.db.graffiti_entries:
            # No graffiti left - delete this object
            self.delete()
        else:
            self.db.desc = "The walls are covered with graffiti in various colors and styles."
            # Ensure integration is active when graffiti exists
            self.db.integrate = True
    
    def return_appearance(self, looker, **kwargs):
        """
        Show graffiti entries when examined.
        
        Args:
            looker (Object): The one looking at the graffiti
            
        Returns:
            str: Formatted appearance
        """
        if not self.db.graffiti_entries:
            # This shouldn't happen since empty objects get deleted,
            # but just in case...
            return "The walls are clean and free of graffiti."
        
        # Header
        appearance = ["Daubed on the walls you see:"]
        
        # Add entries in chronological order (oldest first)
        for entry in self.db.graffiti_entries:
            if entry['message'].strip():  # Only show entries with content
                appearance.append(entry['entry'])
        
        return "\n".join(appearance)
