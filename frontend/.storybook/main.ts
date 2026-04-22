import type { StorybookConfig } from "@storybook/react-webpack5";
import path from "path";

// DEBT-CI-storybook: o builder webpack5 puro do Storybook não inclui loader
// TypeScript — stories .tsx falhavam com "Module parse failed: Unexpected token"
// ao encontrar type imports. Tentar @storybook/nextjs v8.6 não funciona no projeto
// porque Next 16 removeu next/config (dependência interna do preset).
//
// Solução: registrar babel-loader com preset-typescript + preset-react (todos
// já em node_modules via next/react deps). Custo zero em tempo de instalação.
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
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    config.module.rules.push({
      test: /\.(ts|tsx)$/,
      exclude: /node_modules/,
      use: [
        {
          loader: require.resolve("babel-loader"),
          options: {
            babelrc: false,
            configFile: false,
            presets: [
              [
                require.resolve("@babel/preset-env"),
                { targets: { esmodules: true } },
              ],
              [
                require.resolve("@babel/preset-react"),
                { runtime: "automatic" },
              ],
              require.resolve("@babel/preset-typescript"),
            ],
          },
        },
      ],
    });
    return config;
  },
};

export default config;
