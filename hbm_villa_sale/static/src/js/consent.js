/* Consentement aux cookies de mesure : GTM n'est chargé qu'après acceptation explicite. */
(function (root) {
    "use strict";
    var KEY = "hbm_consent";

    function readChoice(storage) {
        try {
            var value = storage.getItem(KEY);
            return value === "granted" || value === "denied" ? value : null;
        } catch (e) {
            return null;
        }
    }

    function saveChoice(storage, value) {
        try {
            storage.setItem(KEY, value);
        } catch (e) {
            /* stockage bloqué : le choix vaut pour cette page seulement */
        }
    }

    /* "none" : rien à faire ; "ask" : afficher le bandeau ; "load" : charger GTM. */
    function decide(gtmId, choice) {
        if (!gtmId) {
            return "none";
        }
        if (choice === "granted") {
            return "load";
        }
        return choice === "denied" ? "none" : "ask";
    }

    function loadGtm(env, gtmId) {
        if (env.gtmLoaded) {
            return;
        }
        env.gtmLoaded = true;
        env.win.dataLayer = env.win.dataLayer || [];
        env.win.dataLayer.push({ "gtm.start": Date.now(), event: "gtm.js" });
        var script = env.doc.createElement("script");
        script.async = true;
        script.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(gtmId);
        env.doc.head.appendChild(script);
    }

    /* Retirer son consentement : on efface le choix et on recharge, le bandeau se réaffiche. */
    function reset(env) {
        saveChoice(env.storage, "");
        if (env.win.location) {
            env.win.location.reload();
        }
    }

    function init(env) {
        if (env.doc.querySelectorAll) {
            env.doc.querySelectorAll("[data-hbm-consent-reset]").forEach(function (link) {
                link.addEventListener("click", function (event) {
                    event.preventDefault();
                    reset(env);
                });
            });
        }
        var banner = env.doc.getElementById("hbm-consent");
        var gtmId = banner && banner.dataset ? banner.dataset.gtmId : "";
        var action = decide(gtmId, readChoice(env.storage));
        if (action === "load") {
            loadGtm(env, gtmId);
        } else if (action === "ask") {
            banner.hidden = false;
            banner.querySelectorAll("[data-hbm-consent]").forEach(function (button) {
                button.addEventListener("click", function () {
                    var value = button.getAttribute("data-hbm-consent");
                    saveChoice(env.storage, value);
                    banner.hidden = true;
                    if (value === "granted") {
                        loadGtm(env, gtmId);
                    }
                });
            });
        }
    }

    var api = { decide: decide, readChoice: readChoice, saveChoice: saveChoice, reset: reset, init: init, KEY: KEY };
    root.HbmConsent = api;
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
