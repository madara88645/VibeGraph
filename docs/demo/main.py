"""Minimal multi-function demo used for README / docs screen recordings."""

def helper_alpha():
    """Returns a short prefix used when formatting messages."""
    return "Hello"


def helper_beta(label: str) -> str:
    """Builds a human-readable line using helper_alpha."""
    prefix = helper_alpha()
    return f"{prefix}, {label}"


def main():
    """Application entry — chains helpers then prints."""
    line = helper_beta("VibeGraph")
    print(line)


if __name__ == "__main__":
    main()
