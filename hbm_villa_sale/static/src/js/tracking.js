/* Événements de conversion (dataLayer) : poussés seulement si le visiteur a accepté. */
(function (root) {
    "use strict";
    var Consent = root.HbmConsent || (typeof require !== "undefined" ? require("./consent.js") : null);

    function track(win, storage, name) {
        if (Consent.readChoice(storage) !== "granted") {
            return;
        }
        win.dataLayer = win.dataLayer || [];
        win.dataLayer.push({ event: name });
    }

    function init(env) {
        if (env.doc.querySelector('[data-status="ok"]')) {
            track(env.win, env.storage, "generate_lead");
        }
        env.doc.querySelectorAll(".hbm-whatsapp").forEach(function (link) {
            link.addEventListener("click", function () {
                track(env.win, env.storage, "whatsapp_click");
            });
        });
    }

    var api = { track: track, init: init };
    root.HbmTracking = api;
    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }
    if (root.document) {
        root.document.addEventListener("DOMContentLoaded", function () {
            var storage;
            try {
                storage = root.localStorage;
            } catch (e) {
                storage = { getItem: function () { return null; }, setItem: function () {} };
            }
            init({ win: root, doc: root.document, storage: storage });
        });
    }
})(typeof window !== "undefined" ? window : globalThis);
