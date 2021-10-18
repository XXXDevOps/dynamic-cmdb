import Layout from '@/layout'

const serviceRouter = {
  path: '/service',
  component: Layout,
  name: 'Service',
  meta: {
    title: '服务',
    icon: 'table'
  },
  children: [
    {
      path: 'serviceTree',
      component: () => import('@/views/cmdb/service/tree'),
      name: 'serviceTree',
      meta: { title: '服务树' }
    }
  ]
}
export default serviceRouter
