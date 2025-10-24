if not contains "$HOME/workspace/.local/share/../bin" $PATH
    # Prepending path in case a system-installed binary needs to be overridden
    set -x PATH "$HOME/workspace/.local/share/../bin" $PATH
end
