import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          background: '#0D1117',
          surface: '#161B22',
          'surface-variant': '#21262D',
          'on-background': '#F0F6FC',
          'on-surface': '#F0F6FC',
          'on-surface-variant': '#E6EDF3',
          primary: '#58A6FF',
          secondary: '#7EE787',
          accent: '#A371F7',
          error: '#F85149',
          info: '#388BFD',
          success: '#3FB950',
          warning: '#D29922'
        },
        variables: {
          'high-emphasis-opacity': 0.95,
          'medium-emphasis-opacity': 0.8,
          'disabled-opacity': 0.5
        }
      },
      light: {
        dark: false,
        colors: {
          background: '#F6F8FA',
          surface: '#FFFFFF',
          'surface-variant': '#EEF2F6',
          'on-background': '#1F2328',
          'on-surface': '#1F2328',
          'on-surface-variant': '#24292F',
          primary: '#0969DA',
          secondary: '#1A7F37',
          accent: '#8250DF',
          error: '#CF222E',
          info: '#0969DA',
          success: '#1A7F37',
          warning: '#9A6700'
        },
        variables: {
          'high-emphasis-opacity': 0.95,
          'medium-emphasis-opacity': 0.8,
          'disabled-opacity': 0.5
        }
      }
    }
  }
})
