import type { StorybookConfig } from "@storybook/react-webpack5";
import path from "path";

const config: StorybookConfig = {
  stories: [
    "../components/**/*.stories.@(ts|tsx)",
    "../app/**/components/**/*.stories.@(ts|tsx)",
  ],
  addons: ["@storybook/addon-essentials"],
  framework: {
    name: "@storybook/react-webpack5",
    options: {},
  },
  staticDirs: ["../public"],
  typescript: {
    reactDocgen: "react-docgen-typescript",
  },
  webpackFinal: async (config) => {
    if (config.resolve) {
      config.resolve.alias = {
        ...config.resolve.alias,
        "@": path.resolve(__dirname, ".."),
      };
    }
    return config;
  },
};

export default config;
