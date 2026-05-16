/* tslint:disable */
/* eslint-disable */

export function disable_skill(skill_id: string): Promise<void>;

export function enable_skill(skill_id: string): Promise<void>;

export function get_skill(skill_id: string): Promise<any>;

export function init_wasm(): Promise<void>;

export function install_skill(skill_id: string, tar_data: Uint8Array): Promise<any>;

export function list_skills(): Promise<any>;

export function uninstall_skill(skill_id: string): Promise<void>;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly disable_skill: (a: number, b: number) => any;
    readonly enable_skill: (a: number, b: number) => any;
    readonly get_skill: (a: number, b: number) => any;
    readonly init_wasm: () => any;
    readonly install_skill: (a: number, b: number, c: number, d: number) => any;
    readonly list_skills: () => any;
    readonly uninstall_skill: (a: number, b: number) => any;
    readonly wasm_bindgen__convert__closures_____invoke__h7dc484db9856920a: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h1899bcf70de34e6f: (a: number, b: number, c: any, d: any) => void;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_destroy_closure: (a: number, b: number) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
