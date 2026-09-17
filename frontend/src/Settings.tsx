import ThemeSwitcher from "./ThemeSwitcher";
import type { ThemeName } from "./ThemeSwitcher";

type SettingsProps = {
  theme: ThemeName;
  onThemeChange: (theme: ThemeName) => void;
  avatar: string;
  onAvatarChange: (avatar: string) => void;
  isAuthenticated: boolean;
  onSignIn: () => void;
  onSignOut: () => void;
};

export default function Settings({
  theme,
  onThemeChange,
  avatar,
  onAvatarChange,
  isAuthenticated,
  onSignIn,
  onSignOut,
}: SettingsProps) {
  const avatarOptions = ["A", "S", "M", "N", "🙂", "✨"];

  return (
    <section className="settings-page" aria-labelledby="settings-title">
      <div className="settings-page-header">
        <span className="conversation-label">SYSTEM SETTINGS</span>
        <h2 id="settings-title">Settings</h2>
        <p>Customize your workspace, profile, and sign-in preferences.</p>
      </div>

      <div className="settings-page-card">
        <ThemeSwitcher
          theme={theme}
          onChange={onThemeChange}
          variant="dropdown"
        />
        <div className="settings-setting-row">
          <div>
            <strong>Compact layout</strong>
            <span>Use tighter spacing throughout the workspace.</span>
          </div>
          <input type="checkbox" aria-label="Compact layout" />
        </div>
        <div className="settings-setting-row">
          <div>
            <strong>Notification sounds</strong>
            <span>Play a sound when an agent response is ready.</span>
          </div>
          <input type="checkbox" defaultChecked aria-label="Notification sounds" />
        </div>
        <div className="settings-profile-section">
          <strong>Profile photo</strong>
          <span>Choose the avatar shown beside your profile name.</span>
          <div className="avatar-options">
            {avatarOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`avatar-option ${avatar === option ? "selected" : ""}`}
                onClick={() => onAvatarChange(option)}
                aria-label={`Use ${option} as profile photo`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          className={isAuthenticated ? "settings-signout" : "settings-signin"}
          onClick={isAuthenticated ? onSignOut : onSignIn}
        >
          {isAuthenticated ? "Sign out" : "Sign in"}
        </button>
      </div>
    </section>
  );
}
