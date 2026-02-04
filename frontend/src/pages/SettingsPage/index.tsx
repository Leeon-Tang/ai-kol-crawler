import { Card, Typography, Form, Input, InputNumber, Button, Space, message, Tabs } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'

const { Title } = Typography
const { TextArea } = Input

const Settings = () => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: apiService.getConfig,
  })

  const updateMutation = useMutation({
    mutationFn: apiService.updateConfig,
    onSuccess: () => {
      message.success('配置已保存')
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
    onError: () => {
      message.error('保存失败')
    },
  })

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config)
    }
  }, [config, form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      updateMutation.mutate(values)
    })
  }

  const youtubeSettings = (
    <Card>
      <Form form={form} layout="vertical">
        <Form.Item
          label="AI 内容占比阈值"
          name={['youtube', 'ai_content_threshold']}
          tooltip="频道中 AI 相关内容的最低占比"
        >
          <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="最小订阅数"
          name={['youtube', 'min_subscribers']}
          tooltip="频道的最低订阅数要求"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="分析视频数量"
          name={['youtube', 'sample_videos']}
          tooltip="每个频道分析的视频数量"
        >
          <InputNumber min={5} max={50} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="搜索关键词"
          name={['youtube', 'search_keywords']}
          tooltip="用于搜索的关键词列表（每行一个）"
        >
          <TextArea
            rows={6}
            placeholder="AI tutorial&#10;machine learning&#10;deep learning"
          />
        </Form.Item>

        <Form.Item
          label="请求间隔（秒）"
          name={['youtube', 'rate_limit']}
          tooltip="每次请求之间的延迟时间"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Card>
  )

  const githubSettings = (
    <Card>
      <Form form={form} layout="vertical">
        <Form.Item
          label="最小 Followers"
          name={['github', 'min_followers']}
          tooltip="开发者的最低 followers 数要求"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="最小公开仓库数"
          name={['github', 'min_public_repos']}
          tooltip="开发者的最低公开仓库数要求"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="搜索关键词"
          name={['github', 'search_keywords']}
          tooltip="用于搜索的技术关键词列表（每行一个）"
        >
          <TextArea
            rows={6}
            placeholder="machine learning&#10;artificial intelligence&#10;deep learning"
          />
        </Form.Item>

        <Form.Item
          label="GitHub Token"
          name={['github', 'token']}
          tooltip="GitHub Personal Access Token（可选，提高 API 限制）"
        >
          <Input.Password placeholder="ghp_xxxxxxxxxxxx" />
        </Form.Item>

        <Form.Item
          label="请求间隔（秒）"
          name={['github', 'rate_limit']}
          tooltip="每次请求之间的延迟时间"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Card>
  )

  const twitterSettings = (
    <Card>
      <Form form={form} layout="vertical">
        <Form.Item
          label="最小粉丝数"
          name={['twitter', 'min_followers']}
          tooltip="用户的最低粉丝数要求"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="搜索关键词"
          name={['twitter', 'search_keywords']}
          tooltip="用于搜索的关键词列表（每行一个）"
        >
          <TextArea
            rows={6}
            placeholder="AI&#10;MachineLearning&#10;DeepLearning"
          />
        </Form.Item>

        <Form.Item
          label="话题标签"
          name={['twitter', 'hashtags']}
          tooltip="用于搜索的话题标签列表（每行一个，不含 #）"
        >
          <TextArea
            rows={4}
            placeholder="AI&#10;MachineLearning&#10;TechNews"
          />
        </Form.Item>

        <Form.Item
          label="请求间隔（秒）"
          name={['twitter', 'rate_limit']}
          tooltip="每次请求之间的延迟时间"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Card>
  )

  const items = [
    {
      key: 'youtube',
      label: 'YouTube 设置',
      children: youtubeSettings,
    },
    {
      key: 'github',
      label: 'GitHub 设置',
      children: githubSettings,
    },
    {
      key: 'twitter',
      label: 'Twitter 设置',
      children: twitterSettings,
    },
  ]

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2}>系统设置</Title>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={updateMutation.isPending}
          >
            保存配置
          </Button>
        </div>

        <Tabs items={items} />
      </Space>
    </div>
  )
}

export default Settings
