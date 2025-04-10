import React from "react";

export function Input(props) {
  return (
    <input
      {...props}
      className={`p-2 rounded-xl border shadow-sm ${props.className}`}
    />
  );
}
