import * as assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";
import {runInNewContext} from "node:vm";
import {ModuleKind, transpileModule} from "typescript";

const code = transpileModule(readFileSync("src/util/needSubscribe.ts", "utf8"), {
    compilerOptions: {module: ModuleKind.CommonJS},
}).outputText;

test("self-hosted sync works without an account; official cloud keeps its subscription check", () => {
    const exports = {} as {canUseSyncProvider: (provider?: number) => boolean};
    const siyuan = {config: {sync: {provider: 3}}, user: null as null | {userSiYuanProExpireTime: number},
        languages: {_kernel: {29: "Subscribe"}}};
    runInNewContext(code, {exports, window: {siyuan}, require: () => ({})});
    for (const provider of [2, 3, 4]) assert.equal(exports.canUseSyncProvider(provider), true);
    assert.equal(exports.canUseSyncProvider(), true);
    for (const provider of [0, -1, 1, 5]) assert.equal(exports.canUseSyncProvider(provider), false);
    siyuan.user = {userSiYuanProExpireTime: -1};
    assert.equal(exports.canUseSyncProvider(0), true);
});
