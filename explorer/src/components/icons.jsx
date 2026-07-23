import React from 'react';

/**
 * Shared icon set.
 *
 * Every icon is an inline SVG on a 24x24 grid, stroked with `currentColor` so
 * it picks up whatever text colour its container already uses. That keeps the
 * icons in step with the light/dark theme tokens without any per-theme asset.
 *
 * Usage: <IconFunction /> for the default 16px, <IconGhost size={22} /> to
 * resize, `style={{ color: accent }}` to tint.
 */

const BASE_PROPS = {
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.75,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    focusable: 'false',
    'aria-hidden': 'true',
};

const Svg = ({ name, size = 16, className, children, ...rest }) => (
    <svg
        {...BASE_PROPS}
        {...rest}
        data-icon={name}
        width={size}
        height={size}
        className={className ? `vg-icon ${className}` : 'vg-icon'}
    >
        {children}
    </svg>
);

/* ===== Node / code semantics ===== */

export const IconFunction = (props) => (
    <Svg name="function" {...props}>
        <path d="M13 2.5 4.5 14h6.5l-1 7.5L19.5 10H13l1-7.5Z" />
    </Svg>
);

export const IconClass = (props) => (
    <Svg name="class" {...props}>
        <path d="M12 2.5 2.5 7 12 11.5 21.5 7 12 2.5Z" />
        <path d="m2.5 12 9.5 4.5 9.5-4.5" />
        <path d="m2.5 16.8 9.5 4.5 9.5-4.5" />
    </Svg>
);

export const IconEntry = (props) => (
    <Svg name="entry" {...props}>
        <path d="M15 2.8h3.5a2 2 0 0 1 2 2v14.4a2 2 0 0 1-2 2H15" />
        <path d="m9.8 16.8 4.7-4.8-4.7-4.8" />
        <path d="M14.5 12H3.5" />
    </Svg>
);

export const IconBuiltin = (props) => (
    <Svg name="builtin" {...props}>
        <path d="M12 2.6 20.4 7.3v9.4L12 21.4 3.6 16.7V7.3L12 2.6Z" />
        <circle cx="12" cy="12" r="3" />
    </Svg>
);

export const IconPackage = (props) => (
    <Svg name="package" {...props}>
        <path d="M12 2.6 20.5 7v10L12 21.4 3.5 17V7L12 2.6Z" />
        <path d="M3.5 7 12 11.7 20.5 7" />
        <path d="M12 11.7v9.7" />
        <path d="m7.6 4.6 8.6 4.7" />
    </Svg>
);

export const IconImport = (props) => (
    <Svg name="import" {...props}>
        <path d="M9.5 17H7.5a5 5 0 0 1 0-10h2" />
        <path d="M14.5 7h2a5 5 0 0 1 0 10h-2" />
        <path d="M8.2 12h7.6" />
    </Svg>
);

export const IconModule = (props) => (
    <Svg name="module" {...props}>
        <path d="M3 7.4a2 2 0 0 1 2-2h3.7a2 2 0 0 1 1.6.8l1 1.4H19a2 2 0 0 1 2 2v7.9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7.4Z" />
    </Svg>
);

export const IconDot = (props) => (
    <Svg name="dot" {...props}>
        <circle cx="12" cy="12" r="4.6" />
    </Svg>
);

/* ===== Files ===== */

export const IconFile = (props) => (
    <Svg name="file" {...props}>
        <path d="M14 2.6H7.5a2 2 0 0 0-2 2v14.8a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V7.4L14 2.6Z" />
        <path d="M13.8 2.6v5h4.7" />
        <path d="M9 13h6" />
        <path d="M9 16.6h4" />
    </Svg>
);

export const IconFiles = (props) => (
    <Svg name="files" {...props}>
        <path d="M15.4 2.6H10a2 2 0 0 0-2 2v10.6a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V6.2l-3.6-3.6Z" />
        <path d="M15.2 2.6v3.9h3.8" />
        <path d="M5 7.2A2 2 0 0 0 3.5 9.1v10.3a2 2 0 0 0 2 2h8.2" />
    </Svg>
);

/* ===== Navigation & chrome ===== */

export const IconSearch = (props) => (
    <Svg name="search" {...props}>
        <circle cx="10.8" cy="10.8" r="6.8" />
        <path d="m20.4 20.4-4.7-4.7" />
    </Svg>
);

export const IconClose = (props) => (
    <Svg name="close" {...props}>
        <path d="M18 6 6 18" />
        <path d="m6 6 12 12" />
    </Svg>
);

export const IconCheck = (props) => (
    <Svg name="check" {...props}>
        <path d="m19.5 6.5-9.7 10.2L4.5 12" />
    </Svg>
);

export const IconCheckCircle = (props) => (
    <Svg name="check-circle" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m16.2 9.3-5.5 5.7-2.9-2.9" />
    </Svg>
);

export const IconAlertCircle = (props) => (
    <Svg name="alert-circle" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7.6v5" />
        <path d="M12 16.3h.01" />
    </Svg>
);

export const IconInfo = (props) => (
    <Svg name="info" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 16.4v-4.8" />
        <path d="M12 7.9h.01" />
    </Svg>
);

export const IconHelp = (props) => (
    <Svg name="help" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.6 9.5a2.5 2.5 0 0 1 4.9.8c0 1.7-2.5 2.5-2.5 2.5" />
        <path d="M12 16.6h.01" />
    </Svg>
);

export const IconChevronDown = (props) => (
    <Svg name="chevron-down" {...props}>
        <path d="m6 9.5 6 6 6-6" />
    </Svg>
);

export const IconMaximize = (props) => (
    <Svg name="maximize" {...props}>
        <path d="M8 3.5H5.5a2 2 0 0 0-2 2V8" />
        <path d="M16 3.5h2.5a2 2 0 0 1 2 2V8" />
        <path d="M20.5 16v2.5a2 2 0 0 1-2 2H16" />
        <path d="M8 20.5H5.5a2 2 0 0 1-2-2V16" />
    </Svg>
);

export const IconMinimize = (props) => (
    <Svg name="minimize" {...props}>
        <path d="M3.5 8H6a2 2 0 0 0 2-2V3.5" />
        <path d="M20.5 8H18a2 2 0 0 1-2-2V3.5" />
        <path d="M16 20.5V18a2 2 0 0 1 2-2h2.5" />
        <path d="M8 20.5V18a2 2 0 0 0-2-2H3.5" />
    </Svg>
);

export const IconCode = (props) => (
    <Svg name="code" {...props}>
        <path d="m15.8 17.8 6-5.8-6-5.8" />
        <path d="M8.2 6.2 2.2 12l6 5.8" />
    </Svg>
);

/* ===== Ghost Runner ===== */

export const IconGhost = (props) => (
    <Svg name="ghost" {...props}>
        <path d="M4.8 20.4V10.4a7.2 7.2 0 0 1 14.4 0v10l-2.4-1.9-2.4 1.9-2.4-1.9-2.4 1.9-2.4-1.9-2.4 1.9Z" />
        <circle cx="9.4" cy="10.4" r="1" fill="currentColor" stroke="none" />
        <circle cx="14.6" cy="10.4" r="1" fill="currentColor" stroke="none" />
    </Svg>
);

export const IconPlay = (props) => (
    <Svg name="play" {...props}>
        <path d="M7.8 4.8 19.4 12 7.8 19.2V4.8Z" fill="currentColor" />
    </Svg>
);

export const IconPause = (props) => (
    <Svg name="pause" {...props}>
        <rect x="6.5" y="4.5" width="4" height="15" rx="1.4" fill="currentColor" />
        <rect x="13.5" y="4.5" width="4" height="15" rx="1.4" fill="currentColor" />
    </Svg>
);

export const IconReset = (props) => (
    <Svg name="reset" {...props}>
        <path d="M3.2 12a8.8 8.8 0 1 0 2.6-6.2L3 8.4" />
        <path d="M3 3.4v5.2h5.2" />
    </Svg>
);

export const IconSparkles = (props) => (
    <Svg name="sparkles" {...props}>
        <path d="m11.4 3.2 1.8 4.4 4.4 1.8-4.4 1.8-1.8 4.4-1.8-4.4L5.2 9.4l4.4-1.8 1.8-4.4Z" />
        <path d="m18.2 14.6.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9.9-2.1Z" />
    </Svg>
);

export const IconNetwork = (props) => (
    <Svg name="network" {...props}>
        <circle cx="18" cy="5.4" r="2.6" />
        <circle cx="6" cy="12" r="2.6" />
        <circle cx="18" cy="18.6" r="2.6" />
        <path d="m8.3 10.7 7.4-4" />
        <path d="m8.3 13.3 7.4 4" />
    </Svg>
);

export const IconShuffle = (props) => (
    <Svg name="shuffle" {...props}>
        <path d="M16.4 3.4h4.2v4.2" />
        <path d="M3.4 20.6 20.6 3.4" />
        <path d="M20.6 16.4v4.2h-4.2" />
        <path d="m15 15 5.6 5.6" />
        <path d="M3.4 3.4 9 9" />
    </Svg>
);

export const IconCompass = (props) => (
    <Svg name="compass" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m15.6 8.4-2.1 5.1-5.1 2.1 2.1-5.1 5.1-2.1Z" />
    </Svg>
);

export const IconChat = (props) => (
    <Svg name="chat" {...props}>
        <path d="M20.8 11.6a8.2 8.2 0 0 1-8.8 8.2 9 9 0 0 1-3.6-.8L3.2 20.8l1.8-5.2a8.2 8.2 0 0 1-.8-3.6 8.2 8.2 0 0 1 8.2-8.2 8.2 8.2 0 0 1 8.4 7.8Z" />
    </Svg>
);

/* ===== Explanation panel & status ===== */

export const IconBook = (props) => (
    <Svg name="book" {...props}>
        <path d="M12 7.4v12" />
        <path d="M3 5.4h4.8a4 4 0 0 1 4.2 2 4 4 0 0 1 4.2-2H21v12h-4.8a4 4 0 0 0-4.2 2 4 4 0 0 0-4.2-2H3V5.4Z" />
    </Svg>
);

export const IconLightbulb = (props) => (
    <Svg name="lightbulb" {...props}>
        <path d="M12 2.6a6.2 6.2 0 0 0-3.6 11.2c.6.5 1 1.2 1 2h5.2c0-.8.4-1.5 1-2A6.2 6.2 0 0 0 12 2.6Z" />
        <path d="M9.6 19.2h4.8" />
        <path d="M10.6 21.6h2.8" />
    </Svg>
);

export const IconSettings = (props) => (
    <Svg name="settings" {...props}>
        <circle cx="12" cy="12" r="3.3" />
        <path d="M12 2.6v2.3M12 19.1v2.3M21.4 12h-2.3M4.9 12H2.6M18.6 5.4l-1.6 1.6M7 17l-1.6 1.6M18.6 18.6 17 17M7 7 5.4 5.4" />
    </Svg>
);

export const IconAlert = (props) => (
    <Svg name="alert" {...props}>
        <path d="M10.3 3.9 1.9 18a2 2 0 0 0 1.7 3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
        <path d="M12 9.2v4.2" />
        <path d="M12 17.2h.01" />
    </Svg>
);

export const IconKey = (props) => (
    <Svg name="key" {...props}>
        <circle cx="7.8" cy="16.2" r="4.2" />
        <path d="M10.8 13.2 20.6 3.4" />
        <path d="m16.4 7.6 2.8 2.8" />
        <path d="m14 10 2.8 2.8" />
    </Svg>
);

export const IconEdit = (props) => (
    <Svg name="edit" {...props}>
        <path d="M16.8 3.4a2.7 2.7 0 0 1 3.8 3.8L7.6 20.2 2.6 21.4l1.2-5L16.8 3.4Z" />
        <path d="m15.2 5 3.8 3.8" />
    </Svg>
);

export const IconClock = (props) => (
    <Svg name="clock" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5.2l3.4 2" />
    </Svg>
);

export const IconPlug = (props) => (
    <Svg name="plug" {...props}>
        <path d="M9.2 2.6v5.2" />
        <path d="M14.8 2.6v5.2" />
        <path d="M5.6 7.8h12.8v3.1a6.4 6.4 0 0 1-12.8 0V7.8Z" />
        <path d="M12 17.3v4.1" />
    </Svg>
);

export const IconGlobe = (props) => (
    <Svg name="globe" {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M3.2 12h17.6" />
        <path d="M12 3a13.6 13.6 0 0 1 0 18 13.6 13.6 0 0 1 0-18Z" />
    </Svg>
);

export const IconRefresh = (props) => (
    <Svg name="refresh" {...props}>
        <path d="M3.2 12a8.8 8.8 0 0 1 14.9-6.3L20.8 8" />
        <path d="M20.8 3.4v4.8H16" />
        <path d="M20.8 12a8.8 8.8 0 0 1-14.9 6.3L3.2 16" />
        <path d="M3.2 20.6v-4.8H8" />
    </Svg>
);

/* ===== Type-driven lookup =====
 * Single source of truth so the node, the sidebar, the search results and the
 * explanation panel never drift apart on what a "class" looks like.
 */

const NODE_TYPE_ICONS = {
    function: IconFunction,
    class: IconClass,
    entry_point: IconEntry,
    builtin: IconBuiltin,
    external: IconPackage,
    imported_local: IconImport,
    module: IconModule,
    unresolved: IconHelp,
    default: IconDot,
};

export const NodeTypeIcon = ({ type, ...props }) => {
    const Icon = NODE_TYPE_ICONS[type] || NODE_TYPE_ICONS.default;
    return <Icon {...props} />;
};
