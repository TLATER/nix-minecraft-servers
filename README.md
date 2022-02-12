# nix-minecraft-servers

Manage Minecraft servers with [nix](https://nixos.org/)!

This is still WIP, almost none of the actual functionality is
implemented. Treat this as a kind of information dump with an initial
design spec hidden in it.

This very explicitly will not implement anything for client-side
use. There are better user-facing interfaces, and a lot of these
projects rely on users downloading them via ad-displaying services.

This intends to make server management easier, which hopefully will
help increase the number of users downloading mods via means approved
by their upstreams.

## Modloaders

### Regarding forge

Forge is distributed as an installer, which downloads all kinds of
libraries when run. This is the definition of impure.

Luckily, this distribution also includes a list of the libraries it
will download in a convenient JSON file. We can use this to determine
what the installer will want to download, and provide the dependencies
for it before it attempts to do so (to my knowledge, this will skip
the download step; if not we can hopefully work with upstream to
change that, or patch the binary downstream).

Forge does kindly ask that the installation process is not automated,
however this is specifically so that they can get users to visit their
download page and display ads to them.

We will therefore **not** download the forge installer itself, and use
nix' store-add feature, requiring users to download the installer at
least once themselves.

The intention is to keep a database of libraries required for each
version of forge, and match the version requested by a user against
this, then to download the required libraries and produce a derivation
of running the forge installer in a directory with these
dependencies. This will allow it to extract its own jar and patch
Minecraft, resulting in download-less forge installation.

Unfortunately, the Minecraft patching process appears to still be
impure, but at least all inputs will be accounted for (and *perhaps*
the MPC team will in the future solve their reproducibility issues).

### Regarding fabric

I have not yet hosted a server using this mod loader, so I have no
experience with it.

## Regarding mods

Mods are generally hosted on
https://www.curseforge.com/minecraft. While they are an integral
component of gameplay for most people still playing this game, them
being tied to this platform is a bit problematic. curseforge is
presumably unable to comfortably handle all the requests to their
platform, and therefore make it quite awkward to try and automatically
pull anything from there (their attempt at monetizing the platform
through the "twitch launcher" probably doesn't help).

Yet this is exactly what we want to do. Mods come in two shapes,
either as mod packs or as individual mod files. Here's how these are
handled:

### Modpacks

Modpacks are pre-configured, pre-collected sets of mods. Think of them
as analogous to Linux distributions. In theory, a manifest file format
exists to define these modpacks that can be used to define the mods
that need to be installed, and it is distributed with a zip file
containing "overrides" which add additional things like configuration
files, server icons and scripts.

Conveniently, this is a json format! Inconveniently, it is entirely
proprietary, with no public documentation, and the only real
implementation that can create or read these is an electron-based web
app (the aforementioned "twitch launcher"). This means that, unless
you are curseforge you practically must have a personal twitch account
and be using their "twitch launcher" to install modpacks (attempts of
using anything else may be thwarted by cloudflare).

This obviously doesn't work well on servers.

It seems that some people upstream noticed this as well, and a pattern
emerges: Most (but not all) modpacks provide a second set of
pre-configured "server" directories, which simply contain a full,
working Minecraft server directory.

Conveniently, this puts the whole ordeal under a single download,
which makes it easier to evade bans from cloudflare.

Inconveniently, these are entirely created to the modpack author's
whims. Some include software which explicitly cannot be redistributed
this way according to their licenses (e.g. the forge installer, which
is present in almost all of these, but explicitly forbids
redistribution because it has a special license from a group of
Minecraft modders who write special tools to patch the Minecraft
binary so that Forge can hook into it; but themselves are
proprietary). Some include BAT scripts to install and run the
server. Some include installers.

All of that is a long way to say that we are stuck with two incredibly
problematic formats for modpacks:

#### manifest.json

Currently unsupported; Modpacks I am interested in don't use this, and
I'm not keen on wading through this. However, some thoughts for a
potential future implementation:

- Manifests do not contain full download links, only project IDs
- We cannot maintain purity and download files from links produced
  after a `fetchurl`, especially if we want to avoid [IFD][IFD].
- We *can* pre-download the manifest with a script, and keep it
  downstream.

Rough algorithm might be:

1. Add a new download script that:
   - Extracts `manifest.json` from a modpack.
   - Creates a json file with an array of (project, id, filename)
     tuples as expected by `fetchModFromCurseForge`.
     - [This example][api-example] of their "API" may help extract the
       filename, which is not recorded in the manifest but required
       for downloads.
   - Also stores a reference to the original modpack so that we can
     access the "overrides".
2. Add a new library function that:
   - Downloads all files in one of the above json files with
     `fetchModFromCurseForge`.
   - Allows user overrides with additional mods and arbitrary
     configuration.
   - Stitches all the above together into a proper Minecraft
     directory, giving priority to user overrides.

### "Server files"

Since these are entirely arbitrary, there is not too much we can
do. We'll assume the following:

- Some `forge-${version}-installer.jar` exists
  - Again, yes, somehow modpacks redistribute this, both against the
    licensing and forge's wishes.
- Some `server.properties` exists
- No `whitelist.json`, `ops.json` or `eula.txt` exist

A proper installation therefore requires that we know the forge
version to be installed before the derivation is built, and inject the
correct set of libraries before the download.

---

[api-example]: https://addons-ecs.forgesvc.net/api/v2/addon/238222
[IFD]: https://nixos.wiki/wiki/Import_From_Derivation
