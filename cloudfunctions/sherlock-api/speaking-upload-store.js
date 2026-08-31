'use strict'

function createSpeakingUploadStore(app) {
  return {
    async upload(path, bytes) {
      return app.uploadFile({ cloudPath: path, fileContent: bytes })
    },
    async download(fileId) {
      const response = await app.downloadFile({ fileID: fileId })
      if (!Buffer.isBuffer(response?.fileContent)) throw new Error('SPEAKING_UPLOAD_INCOMPLETE')
      return response.fileContent
    },
    async remove(fileIds) {
      if (fileIds.length > 0) await app.deleteFile({ fileList: fileIds })
    }
  }
}

module.exports = { createSpeakingUploadStore }
