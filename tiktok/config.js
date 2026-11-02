// The TikTok app's PUBLIC client key (not a secret) and the bot address. The client secret never appears on this site:
// the bot (Google Apps Script) holds it and exchanges the authorization code.
window.ASL_TIKTOK = {
  clientKey: "sbaw0at8953mt8q6mi",
  scope: "user.info.basic,video.upload",
  redirectUri: "https://asl-alhekaya.github.io/tiktok/callback.html",
  bot: "https://script.google.com/macros/s/AKfycbxcSL9ORmrW9xwwMJo5xO6_0vxy50Rz9HURme91nAqNvxeYshOzQz5Mhv5kP1Tfo2jP/exec"
};
