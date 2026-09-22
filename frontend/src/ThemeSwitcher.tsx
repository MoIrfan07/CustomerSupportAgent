import { Check, ChevronDown, Palette, Sun } from "lucide-react";
import { useState } from "react";
import "./ThemeSwitcher.css";

export type ThemeName = "light" | "ocean" | "sunset";

type ThemeSwitcherProps = {
  theme: ThemeName;
  onChange: (theme: ThemeName) => void;
  variant?: "list" | "dropdown";
};

const themes: Array<{
  name: ThemeName;
  label: string;
  description: string;
  icon: typeof Sun;
}> = [
    {
      name: "light",
      label: "Light",
      description: "Clean and bright",
      icon: Sun,
    },
    {
      name: "ocean",
      label: "Ocean",
      description: "Cool blue tones",
      icon: Palette,
    },
    {
      name: "sunset",
      label: "Sunset",
      description: "Warm purple tones",
      icon: Palette,
    },
  ];

export default function ThemeSwitcher({
  theme,
  onChange,
  variant = "list",
}: ThemeSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (variant === "dropdown") {
    const selectedTheme = themes.find((item) => item.name === theme) ?? themes[0];
    const SelectedIcon = selectedTheme.icon;

    return (
      <div
        className={`theme-switcher theme-switcher-dropdown ${
          isOpen ? "open" : ""
        }`}
        aria-label="Choose color theme"
      >
        <div className="theme-switcher-title">Theme</div>
        <button
          type="button"
          className="theme-dropdown-trigger"
          onClick={() => setIsOpen((visible) => !visible)}
          aria-expanded={isOpen}
        >
          <span className={`theme-swatch theme-swatch-${theme}`}>
            <SelectedIcon size={15} />
          </span>
          <span className="theme-option-copy">
            <strong>{selectedTheme.label}</strong>
            <span>{selectedTheme.description}</span>
          </span>
          <ChevronDown size={16} className="theme-dropdown-chevron" />
        </button>
        {isOpen && (
          <div className="theme-dropdown-options">
            {themes.map(({ name, label, description, icon: Icon }) => (
              <button
                key={name}
                type="button"
                className={`theme-option ${theme === name ? "selected" : ""}`}
                onClick={() => {
                  onChange(name);
                  setIsOpen(false);
                }}
                aria-pressed={theme === name}
              >
                <span className={`theme-swatch theme-swatch-${name}`}>
                  <Icon size={15} />
                </span>
                <span className="theme-option-copy">
                  <strong>{label}</strong>
                  <span>{description}</span>
                </span>
                {theme === name && <Check size={15} className="theme-check" />}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="theme-switcher" role="dialog" aria-label="Choose color theme">
      <div className="theme-switcher-title">Appearance</div>
      <div className="theme-options">
        {themes.map(({ name, label, description, icon: Icon }) => (
          <button
            key={name}
            type="button"
            className={`theme-option ${theme === name ? "selected" : ""}`}
            onClick={() => onChange(name)}
            aria-pressed={theme === name}
          >
            <span className={`theme-swatch theme-swatch-${name}`}>
              <Icon size={15} />
            </span>
            <span className="theme-option-copy">
              <strong>{label}</strong>
              <span>{description}</span>
            </span>
            {theme === name && <Check size={15} className="theme-check" />}
          </button>
        ))}
      </div>
    </div>
  );
}
