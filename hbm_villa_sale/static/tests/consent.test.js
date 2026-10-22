// Tests Node (node --test) : stockage et DOM sont simulés, aucun navigateur requis.
const test = require("node:test");
const assert = require("node:assert");
const HbmConsent = require("../src/js/consent.js");
const HbmTracking = require("../src/js/tracking.js");

function fakeStorage(initial) {
    const data = Object.assign({}, initial);
    return {
        getItem: (k) => (k in data ? data[k] : null),
        setItem: (k, v) => { data[k] = v; },
        data,
    };
}

function fakeEnv(storage, gtmId) {
    const scripts = [];
    const buttons = ["granted", "denied"].map((value) => ({
        value,
        handlers: {},
        getAttribute: (name) => (name === "data-hbm-consent" ? value : null),
        addEventListener(type, fn) { this.handlers[type] = fn; },
    }));
    const banner = {
        hidden: true,
        dataset: gtmId ? { gtmId } : {},
        querySelectorAll: () => buttons,
    };
    const doc = {
        head: { appendChild: (el) => scripts.push(el) },
        createElement: () => ({}),
        getElementById: (id) => (id === "hbm-consent" ? banner : null),
    };
    return { win: {}, doc, storage, banner, buttons, scripts };
}

test("decide: sans identifiant GTM il n'y a rien à demander", () => {
    assert.strictEqual(HbmConsent.decide("", null), "none");
    assert.strictEqual(HbmConsent.decide("", "granted"), "none");
});

test("decide: sans choix on demande, accepté on charge, refusé on ne charge pas", () => {
    assert.strictEqual(HbmConsent.decide("GTM-X", null), "ask");
    assert.strictEqual(HbmConsent.decide("GTM-X", "granted"), "load");
    assert.strictEqual(HbmConsent.decide("GTM-X", "denied"), "none");
});

test("readChoice: valeur inconnue ou stockage en erreur -> null", () => {
    assert.strictEqual(HbmConsent.readChoice(fakeStorage({ hbm_consent: "peut-etre" })), null);
    const broken = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } };
    assert.strictEqual(HbmConsent.readChoice(broken), null);
    assert.doesNotThrow(() => HbmConsent.saveChoice(broken, "granted"));
});

test("init sans choix: bandeau visible, rien n'est chargé", () => {
    const env = fakeEnv(fakeStorage(), "GTM-TEST");
    HbmConsent.init(env);
    assert.strictEqual(env.banner.hidden, false);
    assert.strictEqual(env.scripts.length, 0);
});

test("accepter: choix enregistré, GTM chargé une seule fois, bandeau masqué", () => {
    const env = fakeEnv(fakeStorage(), "GTM-TEST");
    HbmConsent.init(env);
    env.buttons[0].handlers.click();
    env.buttons[0].handlers.click();
    assert.strictEqual(env.storage.data.hbm_consent, "granted");
    assert.strictEqual(env.scripts.length, 1);
    assert.match(env.scripts[0].src, /googletagmanager\.com\/gtm\.js\?id=GTM-TEST/);
    assert.strictEqual(env.banner.hidden, true);
});

test("refuser: choix enregistré, rien n'est chargé", () => {
    const env = fakeEnv(fakeStorage(), "GTM-TEST");
    HbmConsent.init(env);
    env.buttons[1].handlers.click();
    assert.strictEqual(env.storage.data.hbm_consent, "denied");
    assert.strictEqual(env.scripts.length, 0);
    assert.strictEqual(env.banner.hidden, true);
});

test("init avec consentement déjà donné: charge sans réafficher le bandeau", () => {
    const env = fakeEnv(fakeStorage({ hbm_consent: "granted" }), "GTM-TEST");
    HbmConsent.init(env);
    assert.strictEqual(env.scripts.length, 1);
    assert.strictEqual(env.banner.hidden, true);
});

test("sans identifiant GTM le bandeau reste caché et rien ne se charge", () => {
    const env = fakeEnv(fakeStorage(), "");
    HbmConsent.init(env);
    assert.strictEqual(env.banner.hidden, true);
    assert.strictEqual(env.scripts.length, 0);
});

test("tracking: aucun événement sans consentement", () => {
    const win = { dataLayer: [] };
    HbmTracking.track(win, fakeStorage(), "generate_lead");
    HbmTracking.track(win, fakeStorage({ hbm_consent: "denied" }), "generate_lead");
    assert.strictEqual(win.dataLayer.length, 0);
});

test("tracking: événement poussé après consentement", () => {
    const win = {};
    HbmTracking.track(win, fakeStorage({ hbm_consent: "granted" }), "whatsapp_click");
    assert.deepStrictEqual(win.dataLayer, [{ event: "whatsapp_click" }]);
});

test("tracking init: generate_lead sur la page de confirmation, whatsapp_click au clic", () => {
    const click = {};
    const link = { addEventListener: (type, fn) => { click[type] = fn; } };
    const doc = {
        querySelector: (sel) => (sel === '[data-status="ok"]' ? {} : null),
        querySelectorAll: (sel) => (sel === ".hbm-whatsapp" ? [link] : []),
    };
    const win = { dataLayer: [] };
    HbmTracking.init({ win, doc, storage: fakeStorage({ hbm_consent: "granted" }) });
    assert.deepStrictEqual(win.dataLayer, [{ event: "generate_lead" }]);
    click.click();
    assert.deepStrictEqual(win.dataLayer[1], { event: "whatsapp_click" });
});
