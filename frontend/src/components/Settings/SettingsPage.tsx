import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Switch,
  Slider,
  Button,
  Avatar,
  Radio,
  Image,
  Divider,
  message,
  Upload,
} from 'antd'
import type { UploadFile, UploadProps } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import {
  UserOutlined,
  BgColorsOutlined,
  SoundOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { ThemeColor } from '@/types'
import { THEME_COLORS, BUILT_IN_BACKGROUNDS, BUILT_IN_SOUNDS } from '@/config/theme'
import {
  themeStorage,
  backgroundStorage,
  enableAlertStorage,
  enableSoundStorage,
  alertMinutesStorage,
  alertSoundStorage,
} from '@/utils/storage'
import { useAppStore } from '@/store'
import './SettingsPage.css'

const { Dragger } = Upload

export const SettingsPage: React.FC = () => {
  const { settings, updateSettings, theme, setTheme, background, setBackground } =
    useAppStore()
  const [form] = Form.useForm()

  const [selectedBg, setSelectedBg] = useState(background)
  const [selectedSound, setSelectedSound] = useState(settings.alertSound)
  const [enableAlert, setEnableAlert] = useState(settings.enableAlert)
  const [enableSound, setEnableSound] = useState(settings.enableSound)
  const [alertMinutes, setAlertMinutes] = useState(settings.alertMinutes)

  const [avatarFileList, setAvatarFileList] = useState<UploadFile[]>([])
  const [avatarPreview, setAvatarPreview] = useState<string>(settings.avatar)

  const [audioFileList, setAudioFileList] = useState<UploadFile[]>([])

  const mockUpload = async (file: File): Promise<string> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const url = URL.createObjectURL(file)
        resolve(url)
      }, 1000)
    })
  }

  const handleAvatarUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options

    try {
      const url = await mockUpload(file as File)
      setAvatarPreview(url)
      updateSettings({ avatar: url })
      onSuccess?.(url)
      message.success('头像上传成功')
    } catch (error) {
      onError?.(error as Error)
      message.error('头像上传失败')
    }
  }

  const handleSoundUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options

    try {
      const url = await mockUpload(file as File)
      setSelectedSound(url)
      updateSettings({ alertSound: url })
      onSuccess?.(url)
      message.success('音频上传成功')
    } catch (error) {
      onError?.(error as Error)
      message.error('音频上传失败')
    }
  }

  const beforeAvatarUpload = (file: File) => {
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件！')
      return Upload.LIST_IGNORE
    }
    const isLt2M = file.size / 1024 / 1024 < 2
    if (!isLt2M) {
      message.error('图片大小不能超过 2MB！')
      return Upload.LIST_IGNORE
    }
    return true
  }

  const beforeSoundUpload = (file: File) => {
    const isAudio = file.type.startsWith('audio/')
    if (!isAudio) {
      message.error('只能上传音频文件！')
      return Upload.LIST_IGNORE
    }
    const isLt5M = file.size / 1024 / 1024 < 5
    if (!isLt5M) {
      message.error('音频大小不能超过 5MB！')
      return Upload.LIST_IGNORE
    }
    return true
  }

  const handleSaveSettings = async () => {
    try {
      const values = await form.validateFields()
      updateSettings({
        nickname: values.nickname,
      })
      themeStorage.set(theme)
      backgroundStorage.set(selectedBg)
      enableAlertStorage.set(enableAlert)
      enableSoundStorage.set(enableSound)
      alertMinutesStorage.set(alertMinutes)
      alertSoundStorage.set(selectedSound)
      message.success('设置已保存')
    } catch (error) {
      message.error('保存失败，请检查输入')
    }
  }

  return (
    <div className="settings-page">
      <h1 className="settings-title">用户设置</h1>

      <div className="settings-content">
        {/* 基本信息 */}
        <Card
          title={
            <span>
              <UserOutlined /> 基本信息
            </span>
          }
          className="settings-card"
        >
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              nickname: settings.nickname,
            }}
          >
            <Form.Item label="昵称" name="nickname">
              <Input placeholder="请输入昵称" maxLength={20} />
            </Form.Item>

            <Form.Item label="头像">
              <div className="avatar-section">
                <Avatar size={80} src={avatarPreview} icon={<UserOutlined />} />
                <div className="avatar-actions">
                  <Upload
                    name="avatar"
                    fileList={avatarFileList}
                    customRequest={handleAvatarUpload}
                    beforeUpload={beforeAvatarUpload}
                    onChange={({ fileList }) => setAvatarFileList(fileList)}
                    showUploadList={false}
                    accept="image/png,image/jpeg,image/jpg"
                  >
                    <Button icon={<InboxOutlined />}>选择头像</Button>
                  </Upload>
                  <p className="avatar-hint">
                    支持 PNG、JPG 格式，文件大小不超过 2MB
                  </p>
                </div>
              </div>
            </Form.Item>
          </Form>
        </Card>

        {/* 主题设置 */}
        <Card
          title={
            <span>
              <BgColorsOutlined /> 主题设置
            </span>
          }
          className="settings-card"
        >
          <div className="theme-section">
            <h3>主题颜色</h3>
            <Radio.Group
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              className="theme-selector"
            >
              {Object.values(THEME_COLORS).map((t) => (
                <Radio.Button
                  key={t.name}
                  value={t.name}
                  style={{
                    backgroundColor: t.primary,
                    color: 'white',
                    borderColor: t.primary,
                  }}
                >
                  {t.displayName}
                </Radio.Button>
              ))}
            </Radio.Group>
          </div>

          <Divider />

          <div className="background-section">
            <h3>背景图片</h3>
            <div className="background-selector">
              {BUILT_IN_BACKGROUNDS.map((bg) => (
                <div
                  key={bg.id}
                  className={`background-option ${selectedBg === bg.path ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedBg(bg.path)
                    setBackground(bg.path)
                  }}
                >
                  {bg.path ? (
                    <Image src={bg.path} alt={bg.name} preview={false} />
                  ) : (
                    <div className="no-background">无背景</div>
                  )}
                  <span>{bg.name}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* 提醒设置 */}
        <Card
          title={
            <span>
              <BellOutlined /> 提醒设置
            </span>
          }
          className="settings-card"
        >
          <Form layout="vertical">
            <Form.Item label="启用紧急提醒">
              <Switch
                checked={enableAlert}
                onChange={setEnableAlert}
                checkedChildren="开启"
                unCheckedChildren="关闭"
              />
            </Form.Item>

            <Form.Item label="启用提醒音效">
              <Switch
                checked={enableSound}
                onChange={setEnableSound}
                checkedChildren="开启"
                unCheckedChildren="关闭"
              />
            </Form.Item>

            {enableSound && (
              <>
                <Form.Item label="提醒音效">
                  <div className="sound-selector">
                    {BUILT_IN_SOUNDS.map((sound) => (
                      <div
                        key={sound.id}
                        className={`sound-option ${selectedSound === sound.path ? 'selected' : ''}`}
                        onClick={() => setSelectedSound(sound.path)}
                      >
                        <SoundOutlined />
                        <span>{sound.name}</span>
                      </div>
                    ))}
                  </div>
                </Form.Item>

                <Form.Item label="自定义音频">
                  <Dragger
                    name="audio"
                    fileList={audioFileList}
                    customRequest={handleSoundUpload}
                    beforeUpload={beforeSoundUpload}
                    onChange={({ fileList }) => setAudioFileList(fileList)}
                    accept="audio/*"
                    maxCount={1}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
                    <p className="ant-upload-hint">
                      支持 MP3、WAV 等音频格式，文件大小不超过 5MB
                    </p>
                  </Dragger>
                </Form.Item>
              </>
            )}

            <Form.Item label={`提前提醒时间: ${alertMinutes} 分钟`}>
              <Slider
                min={5}
                max={60}
                step={5}
                value={alertMinutes}
                onChange={setAlertMinutes}
                marks={{
                  5: '5分',
                  15: '15分',
                  30: '30分',
                  60: '60分',
                }}
              />
            </Form.Item>
          </Form>
        </Card>

        <div className="settings-actions">
          <Button
            type="primary"
            size="large"
            onClick={handleSaveSettings}
            style={{ width: 200 }}
          >
            保存设置
          </Button>
        </div>
      </div>
    </div>
  )
}
