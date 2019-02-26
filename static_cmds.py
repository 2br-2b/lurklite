#!/usr/bin/python3
#
# "Static" commands
#

import miniirc, os, sys, tempcmds, time

commands   = {}
prefs      = {}
tempcmd_db = None

# Register commands
def register_command(*cmds, requires_admin = False):
    def n(func):
        if requires_admin:
            def wrap_cmd(irc, hostmask, is_admin, args):
                if is_admin:
                    return func(irc, hostmask, is_admin, args)
                else:
                    irc.msg(args[0], 'Permission denied!')
        else:
            wrap_cmd = func

        for cmd in cmds:
            commands[cmd.lower()] = wrap_cmd

    return n

# A simple version command
@register_command('version')
def _cmd_version(irc, hostmask, is_admin, args):
    irc.msg(args[0], miniirc.version)

# Reboot
@register_command('reboot', requires_admin = True)
def _cmd_reboot(irc, hostmask, is_admin, args):
    irc.notice(args[0], '\x037\x1dRebooting...\x1d')
    print(is_admin, 'ordered me to reboot.')
    time.sleep(0.1)
    os.execvp(sys.argv[0], sys.argv)

# Privs
@register_command('privs', 'privileges')
def _cmd_privs(irc, hostmask, is_admin, args):
    if is_admin:
        irc.msg(args[0], '{}: You are an admin: `{}`.'.format(hostmask[0],
            is_admin))
    else:
        irc.msg(args[0], '{}: You are not an admin!'.format(hostmask[0]))

# Add and remove "tempcmds"
@register_command('tempcmd', 'tempcmds', requires_admin = True)
def _cmd_tempcmd(irc, hostmask, is_admin, args):
    """
    Creates a "tempcmd".
    Usage: tempcmd del <command>
    """

    assert tempcmd_db

    # Handle the arguments
    cmd_type = None
    params = args[-1].split(' ', 2)

    if len(params) > 1 and params[0] == 'add':
        cmd_type = False
        del params[0]

    if len(params) == 3:
        if tempcmds.command_type_exists(params[1]):
            cmd, cmd_type, code = params
        else:
            cmd, code = params[0], ' '.join(params[1:])
    elif len(params) == 2:
        cmd, code = params
    else:
        return irc.msg(args[0], hostmask[0] + ': Invalid syntax!')

    log = prefs.get(irc, {}).get('tempcmd_log')

    # Delete tempcmds
    if cmd_type is None and cmd in ('del', 'delete', 'remove'):
        if code.startswith(tempcmd_db.prefix):
            r_cmd = repr(code)
            cmd   = code[len(tempcmd_db.prefix):]
        else:
            r_cmd = repr(tempcmd_db.prefix + code)
            cmd   = code

        if cmd not in tempcmd_db:
            return irc.msg(args[0], hostmask[0] + ': The command '
                + repr(cmd) + ' does not exist or is not a tempcmd!')

        del tempcmd_db[cmd]
        if log:
            irc.msg(log, 'User {} deleted temporary command {}.'.format(
                repr(is_admin), r_cmd
            ))
        irc.msg(args[0], hostmask[0] + ': Command ' + r_cmd + ' deleted.')
        return

    # Make sure the command does not start with the prefix
    if cmd.startswith(tempcmd_db.prefix):
        r_cmd = repr(cmd)
        cmd   = cmd[len(tempcmd_db.prefix):]
    else:
        r_cmd = repr(tempcmd_db.prefix + cmd)

    # Make sure the command is not a non-tempcmd
    if cmd.lower() in commands:
        return irc.msg(args[0], hostmask[0] + ': The command ' + rcmd +
            ' already exists as a normal command!')

    # Add the command
    verb = 'updated' if cmd in tempcmd_db else 'created'
    c = {'code': code}
    if cmd_type:
        c['type'] = cmd_type
    tempcmd_db[cmd] = c

    # Get the type
    if not cmd_type:
        cmd_type = tempcmd_db[cmd].type

    # Return the message
    if log:
        irc.msg(log, 'User {} {} temporary command {} (of type {}): {}'.format(
            repr(is_admin), verb, r_cmd, repr(cmd_type), repr(code)
        ))
    irc.msg(args[0], '{}: Command {} (of type {}) {}.'.format(
        hostmask[0], r_cmd, repr(cmd_type), verb
    ))
