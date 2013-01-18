from util import hook

@hook.command
def profile(inp):
    ".profile <username> -- links to <username>'s profile on reddit"
    return 'http://reddit.com/user/' + ''.join(inp.split())
