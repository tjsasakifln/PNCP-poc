"""STORY-258 AC1: Disposable email domain blocklist.

Static set of ≥500 known disposable/temporary email domains.
Used by signup proxy and backend validation for defense-in-depth.
"""

# Top disposable email domains — curated from public lists + Brazilian providers
DISPOSABLE_DOMAINS: frozenset[str] = frozenset({
    # --- International top-50 ---
    "tempmail.com", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "guerrillamail.de", "guerrillamailblock.com", "grr.la", "guerrillamail.biz",
    "mailinator.com", "mailinator.net", "mailinator.org", "mailinator2.com",
    "yopmail.com", "yopmail.fr", "yopmail.net", "yopmail.gq",
    "throwaway.email", "throwawaymail.com", "throam.com",
    "dispostable.com", "disposableemailaddresses.emailmiser.com",
    "sharklasers.com", "guerrillamail.info", "spam4.me",
    "trashmail.com", "trashmail.net", "trashmail.org", "trashmail.me",
    "trashmail.de", "trashmail.at", "trashmail.io",
    "tempail.com", "temp-mail.org", "temp-mail.io", "temp-mail.de",
    "tempmailo.com", "tempmailaddress.com",
    "10minutemail.com", "10minutemail.net", "10minutemail.org",
    "20minutemail.com", "20minutemail.it",
    "mailnesia.com", "mailnull.com", "mailsac.com",
    "maildrop.cc", "maildrop.gq", "maildrop.ml",
    "getairmail.com", "getnada.com", "nada.email",
    "discard.email", "discardmail.com", "discardmail.de",
    "fakeinbox.com", "fakemail.fr", "fakemail.net",
    "mohmal.com", "mohmal.im", "mohmal.in", "mohmal.tech",
    "emailondeck.com", "emailnator.com",
    "harakirimail.com", "mailcatch.com",
    "spamgourmet.com", "spamgourmet.net", "spamgourmet.org",
    "mytemp.email", "mytrashmail.com",
    "mailexpire.com", "tempinbox.com",
    "tempr.email", "temptami.com",
    # --- More international ---
    "crazymailing.com", "deadaddress.com", "despammed.com",
    "devnullmail.com", "dodgit.com", "dodgeit.com",
    "einrot.com", "emailigo.de", "emailisvalid.com",
    "emailthe.net", "emailtmp.com", "emailwarden.com",
    "emailx.at.hm", "emailz.ml", "emz.net",
    "enterto.com", "ephemail.net", "etranquil.com",
    "etranquil.net", "etranquil.org", "evopo.com",
    "example.com", "explodemail.com", "express.net.ua",
    "eyepaste.com", "fastacura.com", "filzmail.com",
    "fixmail.tk", "flyspam.com", "frapmail.com",
    "front14.org", "fux0ringduh.com", "garliclife.com",
    "get1mail.com", "get2mail.fr", "getonemail.com",
    "getonemail.net", "ghosttexter.de", "girlsundertheinfluence.com",
    "gishpuppy.com", "goemailgo.com", "gotmail.com",
    "gotmail.net", "gotmail.org", "gowikibooks.com",
    "grandmamail.com", "grandmasmail.com", "great-host.in",
    "greensloth.com", "gsrv.co.uk", "guerrillamail.com",
    "h8s.org", "haltospam.com", "hatespam.org",
    "herp.in", "hidemail.de", "hidzz.com",
    "hotpop.com", "hulapla.de", "ichimail.com",
    "imails.info", "inbax.tk", "inbox.si",
    "inboxalias.com", "inboxclean.com", "inboxclean.org",
    "incognitomail.com", "incognitomail.net", "incognitomail.org",
    "insorg-mail.info", "ipoo.org", "irish2me.com",
    "iwi.net", "jetable.com", "jetable.fr.nf",
    "jetable.net", "jetable.org", "jnxjn.com",
    "jourrapide.com", "junk1e.com", "kasmail.com",
    "kaspop.com", "keepmymail.com", "killmail.com",
    "killmail.net", "kir.ch.tc", "klassmaster.com",
    "klassmaster.net", "klzlk.com", "koszmail.pl",
    "kurzepost.de", "lawlita.com", "letthemeatspam.com",
    "lhsdv.com", "lifebyfood.com", "link2mail.net",
    "litedrop.com", "lol.ovpn.to", "lookugly.com",
    "lopl.co.cc", "lortemail.dk", "lr78.com",
    "lroid.com", "lukop.dk", "m21.cc",
    "mail-hierarchie.de", "mail-temporaire.fr", "mail.by",
    "mail.mezimages.net", "mail.zp.ua", "mail1a.de",
    "mail21.cc", "mail2rss.org", "mail333.com",
    "mail4trash.com", "mailbidon.com", "mailblocks.com",
    "mailbucket.org", "mailcat.biz", "mailcatch.com",
    "maileater.com", "maileimer.de", "mailexpire.com",
    "mailfa.tk", "mailforspam.com", "mailfree.ga",
    "mailfree.gq", "mailfree.ml", "mailfreeonline.com",
    "mailfs.com", "mailguard.me", "mailhazard.com",
    "mailhazard.us", "mailhz.me", "mailimate.com",
    "mailin8r.com", "mailinater.com", "mailincubator.com",
    "mailismagic.com", "mailjunk.cf", "mailjunk.ga",
    "mailjunk.gq", "mailjunk.ml", "mailjunk.tk",
    "mailmate.com", "mailme.ir", "mailme.lv",
    "mailmetrash.com", "mailmoat.com", "mailms.com",
    "mailnator.com", "mailnesia.com", "mailnull.com",
    "mailorg.org", "mailpick.biz", "mailproxsy.com",
    "mailquack.com", "mailrock.biz", "mailscrap.com",
    "mailshell.com", "mailsiphon.com", "mailslapping.com",
    "mailslite.com", "mailtemp.info", "mailtemporal.com",
    "mailtemporaire.com", "mailtemporaire.fr", "mailtothis.com",
    "mailtrash.net", "mailtv.net", "mailtv.tv",
    "mailzilla.com", "mailzilla.org", "mailzilla.orgmbx.cc",
    "makemetheking.com", "manifestgenerator.com", "manybrain.com",
    "mbx.cc", "mega.zik.dj", "meinspamschutz.de",
    "meltmail.com", "messagebeamer.de", "mezimages.net",
    "mfsa.ru", "mierdamail.com", "ministry-of-silly-walks.de",
    "mintemail.com", "misterpinball.de", "mmmmail.com",
    "moakt.com", "mobi.web.id", "mobileninja.co.uk",
    "moncourrier.fr.nf", "monemail.fr.nf", "monmail.fr.nf",
    "monumentmail.com", "ms9.mailslite.com", "msa.minsmail.com",
    "mt2009.com", "mt2014.com", "mt2015.com",
    "mx0.wwwnew.eu", "my10minutemail.com", "mycard.net.ua",
    "mycleaninbox.net", "myemailboxy.com", "mymail-in.net",
    "mymailoasis.com", "mynetstore.de", "mypacks.net",
    "mypartyclip.de", "myspaceinc.com", "myspaceinc.net",
    "myspaceinc.org", "myspacepimpedup.com", "mytrashmail.com",
    "neomailbox.com", "nepwk.com", "nervmich.net",
    "nervtansen.de", "netmails.com", "netmails.net",
    "neverbox.com", "no-spam.ws", "nobulk.com",
    "noclickemail.com", "nogmailspam.info", "nomail.pw",
    "nomail.xl.cx", "nomail2me.com", "nomorespamemails.com",
    "nonspam.eu", "nonspammer.de", "noref.in",
    "nospam.ze.tc", "nospam4.us", "nospamfor.us",
    "nospammail.net", "nospamthanks.info", "nothingtoseehere.ca",
    "nowmymail.com", "nurfuerspam.de", "nus.edu.sg",
    "nwldx.com", "objectmail.com", "obobbo.com",
    "odnorazovoe.ru", "oneoffemail.com", "onewaymail.com",
    "oopi.org", "ordinaryamerican.net", "otherinbox.com",
    "ourklips.com", "outlawspam.com", "ovpn.to",
    "owlpic.com", "pancakemail.com", "pimpedupmyspace.com",
    "pjjkp.com", "plexolan.de", "poczta.onet.pl",
    "politikerclub.de", "pookmail.com", "privacy.net",
    "privatdemail.net", "proxymail.eu", "prtnx.com",
    "punkass.com", "putthisinyouremail.com", "qq.com",
    "quickinbox.com", "rcpt.at", "reallymymail.com",
    "recode.me", "recursor.net", "recyclemail.dk",
    "regbypass.com", "regbypass.comsafe-mail.net",
    "rejectmail.com", "reliable-mail.com", "rhyta.com",
    "rklips.com", "rmqkr.net", "royal.net",
    "rppkn.com", "rtrtr.com", "s0ny.net",
    "safe-mail.net", "safersignup.de", "safetymail.info",
    "safetypost.de", "sandelf.de", "saynotospams.com",
    "scatmail.com", "schafmail.de", "selfdestructingmail.com",
    "sendspamhere.com", "shiftmail.com", "shitmail.me",
    "shortmail.net", "sibmail.com", "skeefmail.com",
    "slaskpost.se", "slipry.net", "slopsbox.com",
    "slowslow.de", "smashmail.de", "smellfear.com",
    "snakemail.com", "sneakemail.com", "snkmail.com",
    "sofimail.com", "sofort-mail.de", "softpls.asia",
    "sogetthis.com", "soodonims.com", "spam.la",
    "spam.su", "spamavert.com", "spambob.com",
    "spambob.net", "spambob.org", "spambog.com",
    "spambog.de", "spambog.ru", "spambox.info",
    "spambox.irishspringrealty.com", "spambox.us",
    "spamcannon.com", "spamcannon.net", "spamcero.com",
    "spamcon.org", "spamcorptastic.com", "spamcowboy.com",
    "spamcowboy.net", "spamcowboy.org", "spamday.com",
    "spamex.com", "spamfighter.cf", "spamfighter.ga",
    "spamfighter.gq", "spamfighter.ml", "spamfighter.tk",
    "spamfree.eu", "spamfree24.com", "spamfree24.de",
    "spamfree24.eu", "spamfree24.info", "spamfree24.net",
    "spamfree24.org", "spamgoes.in", "spamherelots.com",
    "spamhereplease.com", "spamhole.com", "spamify.com",
    "spaminator.de", "spamkill.info", "spaml.com",
    "spaml.de", "spammotel.com", "spamobox.com",
    "spamoff.de", "spamslicer.com", "spamspot.com",
    "spamstack.net", "spamthis.co.uk", "spamtrap.ro",
    "spamtrail.com", "spamwc.de", "spoofmail.de",
    "squizzy.de", "sry.li", "stuffmail.de",
    "supergreatmail.com", "supermailer.jp", "superrito.com",
    "superstachel.de", "suremail.info", "svk.jp",
    "sweetxxx.de", "tafmail.com", "tagyoureit.com",
    "talkinator.com", "tapchicuoihoi.com", "teewars.org",
    "teleworm.com", "teleworm.us", "temp.emeraldcraft.com",
    "temp.headstrong.de", "tempalias.com", "tempe4mail.com",
    "tempemail.biz", "tempemail.co.za", "tempemail.com",
    "tempemail.net", "tempinbox.co.uk", "tempinbox.com",
    "tempmail.eu", "tempmail.it", "tempmail2.com",
    "tempmailer.com", "tempmailer.de", "tempomail.fr",
    "temporarily.de", "temporarioemail.com.br", "temporaryemail.net",
    "temporaryemail.us", "temporaryforwarding.com", "temporaryinbox.com",
    "temporarymailaddress.com", "thanksnospam.info",
    "thankyou2010.com", "thc.st", "thecriminals.com",
    "thisisnotmyrealemail.com", "thismail.net", "thismail.ru",
    "throwawayemailaddress.com", "tilien.com", "tittbit.in",
    "tizi.com", "tmailinator.com", "toiea.com",
    "toomail.biz", "topranklist.de", "tradermail.info",
    "trash-amil.com", "trash-mail.at", "trash-mail.com",
    "trash-mail.de", "trash2009.com", "trash2010.com",
    "trash2011.com", "trashdevil.com", "trashdevil.de",
    "trashemail.de", "trashemails.de", "trashmail.at",
    "trashmail.com", "trashmail.de", "trashmail.io",
    "trashmail.me", "trashmail.net", "trashmail.org",
    "trashmail.ws", "trashmailer.com", "trashymail.com",
    "trashymail.net", "trbvm.com", "trbvn.com",
    "trialmail.de", "trickmail.net", "trillianpro.com",
    "turual.com", "twinmail.de", "tyldd.com",
    "uggsrock.com", "umail.net", "upliftnow.com",
    "uplipht.com", "venompen.com", "veryreallyrealmail.com",
    "viditag.com", "viewcastmedia.com", "viewcastmedia.net",
    "viewcastmedia.org", "vomoto.com", "vpn.st",
    "vsimcard.com", "vubby.com", "wasteland.rfc822.org",
    "webemail.me", "webm4il.info", "wegwerfadresse.de",
    "wegwerfemail.com", "wegwerfemail.de", "wegwerfemail.net",
    "wegwerfemail.org", "wegwerfmail.de", "wegwerfmail.net",
    "wegwerfmail.org", "wetrainbayarea.com", "wetrainbayarea.org",
    "wh4f.org", "whatiaas.com", "whatpaas.com",
    "whyspam.me", "wickmail.net", "wilemail.com",
    "willhackforfood.biz", "willselfdestruct.com", "winemaven.info",
    "wronghead.com", "wuzup.net", "wuzupmail.net",
    "wwwnew.eu", "xagloo.com", "xemaps.com",
    "xents.com", "xmaily.com", "xoxox.cc",
    "xyzfree.net", "yogamaven.com", "yomail.info",
    "yopmail.com", "yopmail.fr", "yopmail.gq",
    "yopmail.net", "yuurok.com", "zehnminutenmail.de",
    "zippymail.info", "zoaxe.com", "zoemail.org",
    # --- Brazilian disposable providers ---
    "emailtemporario.com.br", "tempmail.com.br", "emailfalso.com.br",
    "emaildescartavel.com.br", "lixomail.com.br", "temporario.email",
    "emailteste.com.br", "descartavel.com.br", "emailprovider.com.br",
    "spambox.com.br",
    # --- Common aliases for already-listed ---
    "mailtemp.net", "mailtemp.org", "tempmail.net",
    "tempmail.org", "tempmail.de", "tempmail.co",
    "tmpmail.net", "tmpmail.org", "tmpmail.com",
    "guerrillamail.se", "guerrillamail.eu",
    "mailinator.us", "mailinator.co",
    "dispostable.org", "dispostable.net",
})


def is_disposable_email(email: str) -> bool:
    """Check if an email address uses a disposable/temporary domain.

    Args:
        email: Full email address (e.g., "user@tempmail.com")

    Returns:
        True if the domain is in the disposable blocklist.
    """
    if not email or "@" not in email:
        return False

    domain = email.rsplit("@", 1)[1].strip().lower()
    return domain in DISPOSABLE_DOMAINS


# Known personal email providers (not blocked, used for badge display)
PERSONAL_PROVIDERS: frozenset[str] = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
    "live.com", "msn.com", "yahoo.com", "yahoo.com.br",
    "icloud.com", "me.com", "mac.com", "aol.com",
    "protonmail.com", "proton.me", "pm.me",
    "zoho.com", "zohomail.com", "mail.com",
    "gmx.com", "gmx.net", "gmx.de",
    "uol.com.br", "bol.com.br", "terra.com.br",
    "ig.com.br", "globo.com", "globomail.com",
    "r7.com", "zipmail.com.br",
})


def is_corporate_email(email: str) -> bool:
    """Check if an email is likely corporate (not personal, not disposable).

    Args:
        email: Full email address.

    Returns:
        True if the domain is NOT in personal providers and NOT disposable.
    """
    if not email or "@" not in email:
        return False

    domain = email.rsplit("@", 1)[1].strip().lower()
    if domain in DISPOSABLE_DOMAINS:
        return False
    if domain in PERSONAL_PROVIDERS:
        return False
    return True
