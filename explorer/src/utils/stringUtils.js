export const getShortName = (path) => {
    if (!path) return "";
    const lastSlash = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
    return lastSlash >= 0 ? path.substring(lastSlash + 1) : path;
};
