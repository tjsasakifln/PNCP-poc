/**
 * STORY-298: Framer Motion mock for Jest tests.
 *
 * Renders motion.* components as plain divs and AnimatePresence as a passthrough.
 * This prevents animation delays from interfering with test assertions.
 */
const React = require("react");

const motion = new Proxy(
  {},
  {
    get: (_target, prop) => {
      // motion.div, motion.span, etc. → render as plain HTML element
      return React.forwardRef((props, ref) => {
        // Strip framer-motion-specific props before passing to DOM
        const {
          initial,
          animate,
          exit,
          transition,
          variants,
          whileHover,
          whileTap,
          whileInView,
          whileFocus,
          whileDrag,
          layout,
          layoutId,
          onAnimationStart,
          onAnimationComplete,
          ...rest
        } = props;
        return React.createElement(String(prop), { ...rest, ref });
      });
    },
  },
);

const AnimatePresence = ({ children }) => {
  return React.createElement(React.Fragment, null, children);
};

module.exports = {
  motion,
  AnimatePresence,
  useAnimation: () => ({}),
  useMotionValue: (initial) => ({
    get: () => initial,
    set: () => {},
    onChange: () => () => {},
  }),
  useTransform: (value) => value,
  useSpring: (value) => value,
  useInView: () => [null, true],
};
