from Products.CMFPlone.resources.browser.resource import ResourceView
from urlparse import urlparse
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


class ScriptsView(ResourceView):
    """ Information for script rendering. """

    def get_data(self, bundle, result):
        bundle_name = bundle.__prefix__.split('/', 1)[1].rstrip('.')
        if self.development is False:
            if bundle.compile is False:
                # Its a legacy css bundle
                if not bundle.last_compilation or self.last_legacy_import > bundle.last_compilation:
                    # We need to compile
                    cookWhenChangingSettings(self.context, bundle)
            if bundle.jscompilation:
                result.append({
                    'bundle': bundle_name,
                    'conditionalcomment': bundle.conditionalcomment,
                    'src': '%s/%s?version=%s' % (
                        self.portal_url, bundle.jscompilation,
                        bundle.last_compilation)
                })
        else:
            resources = self.get_resources()
            for resource in bundle.resources:
                if resource in resources:
                    script = resources[resource]
                    if script.js:
                        url = urlparse(script.js)
                        if url.netloc == '':
                            # Local
                            src = "%s/%s" % (self.portal_url, script.js)
                        else:
                            src = "%s" % (script.js)

                        data = {
                            'bundle': bundle_name,
                            'conditionalcomment': bundle.conditionalcomment,  # noqa
                            'src': src}
                        result.append(data)

    def scripts(self):
        """
        The requirejs scripts, the ones that are not resources
        are loaded on configjs.py
        """
        result = []
        # We always add jquery resource
        result.append({
            'src': '%s/%s' % (
                self.portal_url,
                self.registry.records['plone.resources/jquery.js'].value),
            'conditionalcomment': None,
            'bundle': 'basic'
        })
        if self.development:
            # We need to add require.js and config.js
            result.append({
                'src': '%s/%s' % (
                    self.portal_url,
                    self.registry.records['plone.resources.less-variables'].value),  # noqa
                'conditionalcomment': None,
                'bundle': 'basic'
            })
            result.append({
                'src': '%s/%s' % (
                    self.portal_url,
                    self.registry.records['plone.resources.lessc'].value),
                'conditionalcomment': None,
                'bundle': 'basic'
            })
            # result.append({
            #     'src': '%s/%s' % (
            #         self.portal_url,
            #         self.registry.records['plone.resources.less-modify'].value),
            #     'conditionalcomment': None,
            #     'bundle': 'basic'
            # })
        result.append({
            'src': '%s/%s' % (
                self.portal_url,
                self.registry.records['plone.resources.requirejs'].value),
            'conditionalcomment': None,
            'bundle': 'basic'
        })
        result.append({
            'src': '%s/%s' % (
                self.portal_url,
                self.registry.records['plone.resources.configjs'].value),
            'conditionalcomment': None,
            'bundle': 'basic'
        })
        result.extend(self.ordered_bundles_result())

        # Add diazo url
        origin = None
        if self.diazo_production_js and self.development is False:
            origin = self.diazo_production_js
        if self.diazo_development_js and self.development is True:
            origin = self.diazo_development_js
        if origin:
            result.append({
                'bundle': 'diazo',
                'conditionalcomment': '',
                'src': '%s/%s' % (
                    self.portal_url, origin)
            })

        return result
