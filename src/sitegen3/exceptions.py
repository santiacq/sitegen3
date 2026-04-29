class SitegenError(Exception):
    pass


class ConfigError(SitegenError):
    pass


class DiscoveryError(SitegenError):
    pass


class InitError(SitegenError):
    pass


class ServeError(SitegenError):
    pass


class PageError(SitegenError):
    pass


class LoaderError(PageError):
    pass


class RenderError(PageError):
    pass
