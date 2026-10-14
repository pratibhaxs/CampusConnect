import { useState, useEffect, useRef } from "react";

/**
 * Typeable search box that still commits only a real record.
 * options: [{ value, label }]. `value` is the confirmed option value ("" = none).
 * Typing clears the confirmed value; picking a match from the list sets it.
 */
export default function SearchableSelect({ options, value, onChange, placeholder, disabled, required, name, onAddNew }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);

  const selected = options.find((o) => String(o.value) === String(value));

  // keep the visible text in sync with the confirmed value
  useEffect(() => {
    setQuery(selected ? selected.label : "");
  }, [value, options]); // eslint-disable-line react-hooks/exhaustive-deps

  // close on outside click and snap text back to the confirmed label
  useEffect(() => {
    function handleClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
        setQuery(selected ? selected.label : "");
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [selected]);

  const q = query.trim().toLowerCase();
  const filtered = q === "" || (selected && query === selected.label)
    ? options
    : options.filter((o) => o.label.toLowerCase().includes(q));

  function handleInputChange(e) {
    setQuery(e.target.value);
    setOpen(true);
    if (value !== "" && value != null) onChange("");
  }

  const typed = query.trim();
  const canAdd = onAddNew && typed.length >= 2 && !value
    && !options.some((o) => o.label.toLowerCase() === typed.toLowerCase());

  function handleAdd() {
    setOpen(false);
    onAddNew(typed);
  }

  function handleSelect(option) {
    onChange(String(option.value));
    setQuery(option.label);
    setOpen(false);
  }

  return (
    <div className="searchable-select" ref={wrapperRef}>
      <input
        type="text"
        name={name}
        autoComplete="off"
        value={query}
        onChange={handleInputChange}
        onFocus={() => !disabled && setOpen(true)}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
      />
      {open && !disabled && (
        <ul className="searchable-select-list">
          {filtered.length === 0 && !canAdd ? (
            <li className="searchable-select-empty">No matches</li>
          ) : (
            filtered.map((o) => (
              <li key={o.value} onMouseDown={(e) => { e.preventDefault(); handleSelect(o); }}>
                {o.label}
              </li>
            ))
          )}
          {canAdd && (
            <li className="searchable-select-add" onMouseDown={(e) => { e.preventDefault(); handleAdd(); }}>
              + Add “{typed}” as new
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
