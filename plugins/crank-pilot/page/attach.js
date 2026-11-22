import { deleteAttachment, postAttachment } from "/page/api.js";
import { ATTACH_MESSAGES, attachRefusal, sniffImage } from "/page/model.js";
import { el } from "/page/dom.js";

const FAILED = "Could not attach the image. Try again.";
const NOT_REMOVED = "Could not remove the image. Try again.";
export const BUSY = "An image is still uploading or being removed. Try again in a moment.";

// Uploads and removals in flight, across every control: a response sent while one is open would miss or name an image.
let working = 0;
export const attaching = () => working > 0;

const nameOf = (path) => path.split("/").pop();
// The server numbers a stored image `pilot/attachments/<interaction>-<k>.<type>`.
const numberOf = (path) => Number(/-(\d+)\.[a-z]+$/.exec(path)?.[1]);

// True once the server holds no file for `path`: deleted, already gone, or its interaction is no longer pending.
async function deleteImage(interaction, path) {
  working++;
  try {
    const res = await deleteAttachment(interaction, numberOf(path));
    return [204, 404, 409].includes(res.status);
  } catch {
    return false;
  } finally {
    working--;
  }
}

// Deletes every image in `paths`; true when none is left on the server.
export async function discardImages(interaction, paths) {
  return (await Promise.all(paths.map((path) => deleteImage(interaction, path)))).every(Boolean);
}

// The message for a refused upload. A 409 is the cap or an interaction that is no longer pending: the first says so,
// the second says nothing, and the poll moves the page to the interaction that replaced it.
async function refusalFor(res) {
  if (res.status === 415) return ATTACH_MESSAGES.type;
  if (res.status === 413) return ATTACH_MESSAGES.size;
  if (res.status === 409) {
    const body = await res.json().catch(() => ({}));
    return body.error === "ten images are already attached" ? ATTACH_MESSAGES.count : "";
  }
  return FAILED;
}

// A control for the images one holder (a question, a mark, a note, a verdict, a pin) carries. `paths` are the stored
// paths it starts with, `count()` the images on the whole response, and `onChange(paths)` hears every change. Paste and
// drop work anywhere in `zone`, which is `root` unless the caller names a wider element.
export function mountAttach(root, { interaction, paths, count, onChange, zone = root }) {
  let held = [...paths];
  let bound = null;
  const pick = el("label", { class: "atp" });
  pick.innerHTML = '<input type="file" accept="image/*" multiple><span class="bt">Attach image</span>';
  const input = pick.firstChild;
  const list = el("ul", { class: "attlist", "aria-label": "Attached images" });
  const message = el("p", { class: "err", role: "alert" });
  const node = el("div", { class: "att" }, pick, list, message);

  function paint() {
    list.replaceChildren(
      ...held.map((path) => {
        const remove = el("button", { type: "button", "aria-label": `Remove image ${nameOf(path)}` }, "Remove");
        remove.addEventListener("click", () => removeImage(path));
        return el("li", {}, el("span", { class: "fn" }, nameOf(path)), remove);
      }),
    );
  }

  // The holder may redraw around the control when told of a change, which drops focus the user had inside it.
  function commit(next) {
    const had = node.contains(document.activeElement);
    held = next;
    paint();
    onChange(held.slice());
    if (had) input.focus();
  }

  async function removeImage(path) {
    message.textContent = "";
    if (await deleteImage(interaction, path)) commit(held.filter((p) => p !== path));
    else message.textContent = NOT_REMOVED;
  }

  async function upload(file) {
    working++;
    try {
      const res = await postAttachment(interaction, file);
      if (res.status === 201) commit([...held, (await res.json()).path]);
      else message.textContent = await refusalFor(res);
    } catch {
      message.textContent = FAILED;
    } finally {
      working--;
    }
  }

  // One file after another, so each is judged against the count the one before it made.
  async function add(files) {
    message.textContent = "";
    for (const file of files) {
      const kind = sniffImage(new Uint8Array(await file.slice(0, 12).arrayBuffer()));
      const refusal = attachRefusal({ kind, size: file.size, count: count() });
      if (refusal) message.textContent = refusal;
      else await upload(file);
    }
  }

  const gestures = {
    'paste': (event) => {
      const files = [...(event.clipboardData?.files ?? [])];
      if (!files.length) return;
      event.preventDefault();
      add(files);
    },
    'dragover': (event) => {
      if (![...(event.dataTransfer?.types ?? [])].includes("Files")) return;
      event.preventDefault();
      bound.classList.add("drop");
    },
    'dragleave': (event) => {
      if (!bound.contains(event.relatedTarget)) bound.classList.remove("drop");
    },
    'drop': (event) => {
      bound.classList.remove("drop");
      const files = [...(event.dataTransfer?.files ?? [])];
      if (!files.length) return;
      event.preventDefault();
      add(files);
    },
  };
  const bind = (target) => {
    bound = target;
    for (const [type, handler] of Object.entries(gestures)) target.addEventListener(type, handler);
  };
  const unbind = () => {
    for (const [type, handler] of Object.entries(gestures)) bound.removeEventListener(type, handler);
    bound.classList.remove("drop");
  };

  input.addEventListener("change", () => {
    const files = [...input.files];
    input.value = "";
    add(files);
  });

  paint();
  root.append(node);
  bind(zone);

  return {
    node,
    set(next) {
      held = [...next];
      paint();
    },
    // Puts the control into another holder's element, with its list, message, and uploads in flight.
    move(into, within = into) {
      unbind();
      into.append(node);
      bind(within);
    },
  };
}

// The control a holder keeps across redraws of the list it sits in: `cache` maps the holder's key to its control, so an
// upload that began before a redraw still lands on the holder it began on.
export function holderControl(cache, key, root, options) {
  const found = cache.get(key);
  if (found) found.move(root);
  else cache.set(key, mountAttach(root, options));
}
