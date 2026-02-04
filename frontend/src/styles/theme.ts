import { ThemeConfig } from 'antd'

export const lightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f0f2f5',
    colorText: 'rgba(0, 0, 0, 0.88)',
    colorTextSecondary: 'rgba(0, 0, 0, 0.65)',
    colorTextTertiary: 'rgba(0, 0, 0, 0.45)',
    colorBorder: '#d9d9d9',
    borderRadius: 6,
    fontSize: 14,
    fontWeightStrong: 600,
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#ffffff',
      bodyBg: '#f0f2f5',
      headerHeight: 64,
      headerPadding: '0 24px',
    },
    Menu: {
      itemBg: '#ffffff',
      itemSelectedBg: '#e6f7ff',
      itemSelectedColor: '#1890ff',
      itemHoverBg: '#f5f5f5',
      itemHoverColor: '#1890ff',
      itemColor: 'rgba(0, 0, 0, 0.88)',
      subMenuItemBg: '#ffffff',
    },
    Card: {
      colorBgContainer: '#ffffff',
      boxShadowTertiary: '0 2px 8px rgba(0, 0, 0, 0.06)',
    },
    Table: {
      headerBg: '#fafafa',
      headerColor: 'rgba(0, 0, 0, 0.88)',
      rowHoverBg: '#fafafa',
    },
    Button: {
      fontWeight: 500,
    },
  },
}

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorBgContainer: '#1f1f1f',
    colorBgElevated: '#282828',
    colorBgLayout: '#141414',
    colorText: 'rgba(255, 255, 255, 0.88)',
    colorTextSecondary: 'rgba(255, 255, 255, 0.65)',
    colorTextTertiary: 'rgba(255, 255, 255, 0.45)',
    colorBorder: '#303030',
    borderRadius: 6,
    fontSize: 14,
    fontWeightStrong: 600,
  },
  components: {
    Layout: {
      headerBg: '#1f1f1f',
      siderBg: '#000000',
      bodyBg: '#141414',
      headerHeight: 64,
      headerPadding: '0 24px',
    },
    Menu: {
      darkItemBg: '#000000',
      darkItemSelectedBg: '#1890ff',
      darkItemHoverBg: 'rgba(255, 255, 255, 0.08)',
      darkItemColor: 'rgba(255, 255, 255, 0.65)',
      darkItemSelectedColor: '#ffffff',
      darkItemHoverColor: 'rgba(255, 255, 255, 0.88)',
      darkSubMenuItemBg: '#000000',
    },
    Card: {
      colorBgContainer: '#1f1f1f',
      boxShadowTertiary: '0 2px 8px rgba(0, 0, 0, 0.45)',
    },
    Table: {
      colorBgContainer: '#1f1f1f',
      headerBg: '#282828',
      headerColor: 'rgba(255, 255, 255, 0.88)',
      rowHoverBg: '#282828',
      colorText: 'rgba(255, 255, 255, 0.88)',
      colorTextHeading: 'rgba(255, 255, 255, 0.88)',
    },
    Button: {
      fontWeight: 500,
      defaultBg: '#282828',
      defaultBorderColor: '#303030',
      defaultColor: 'rgba(255, 255, 255, 0.88)',
    },
    Input: {
      colorBgContainer: '#262626',
      colorBorder: '#434343',
      colorText: 'rgba(255, 255, 255, 0.88)',
      colorTextPlaceholder: 'rgba(255, 255, 255, 0.45)',
    },
    Select: {
      colorBgContainer: '#262626',
      colorBorder: '#434343',
      colorText: 'rgba(255, 255, 255, 0.88)',
      optionSelectedBg: '#1890ff',
    },
    Tag: {
      defaultBg: 'rgba(255, 255, 255, 0.08)',
      defaultColor: 'rgba(255, 255, 255, 0.88)',
    },
    Slider: {
      trackBg: '#1890ff',
      trackHoverBg: '#40a9ff',
      railBg: 'rgba(255, 255, 255, 0.12)',
      railHoverBg: 'rgba(255, 255, 255, 0.15)',
      handleColor: '#ffffff',
      handleActiveColor: '#ffffff',
      dotBorderColor: '#434343',
      dotActiveBorderColor: '#1890ff',
    },
  },
}

