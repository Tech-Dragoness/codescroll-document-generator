import React from "react";

export function Button({ children, ...props }) {
  return (
    <button
      {...props}
      className={`px-4 py-2 rounded-2xl bg-indigo-600 hover:bg-indigo-400 text-white shadow-md transition-all ${props.className}`}
    >
      {children}
    </button>
  );
}
