/** Image-space hit tests and bounded camera controls, shared with unit tests. */
export const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
export function pointInImage(clientX, clientY, rect, width, height) {
  if (!rect.width || !rect.height) return null;
  const u = (clientX - rect.left) / rect.width;
  const v = (clientY - rect.top) / rect.height;
  if (u < 0 || u >= 1 || v < 0 || v >= 1) return null;
  return { x: Math.floor(u * width), y: Math.floor(v * height) };
}
/** The full room height always fits: no vertical scrolling. Narrow screens pan sideways;
 *  screens wider than the render show the whole room over a blurred backdrop. */
export function fitScene(viewWidth, viewHeight, aspect) {
  return { width: viewHeight * aspect, height: viewHeight };
}
export function frameForAngle(angle, frames) {
  return frames.reduce((best, frame) => Math.abs(frame.angle - angle) < Math.abs(best.angle - angle) ? frame : best).index;
}
export function boundedPan(x, y, size, viewport) {
  const rx = Math.max(0, (size.width - viewport.width) / 2), ry = Math.max(0, (size.height - viewport.height) / 2);
  return { x: clamp(x, -rx, rx) || 0, y: clamp(y, -ry, ry) || 0 };
}
export function hotspotFromPixels(pixels, width, height, point, radius = 0) {
  if (!point) return 0;
  const at = (x, y) => x < 0 || y < 0 || x >= width || y >= height ? 0 : pixels[(y * width + x) * 4];
  const center = at(point.x, point.y);
  if (center || !radius) return center;
  for (let r = 1; r <= radius; r++) {
    for (const [dx, dy] of [[r,0],[-r,0],[0,r],[0,-r],[r,r],[-r,r],[r,-r],[-r,-r]]) {
      const id = at(point.x + dx, point.y + dy);
      if (id) return id;
    }
  }
  return 0;
}
/** Projective transform taking a w×h element onto quad [TL, TR, BR, BL] (CSS px), as a CSS matrix3d. */
export function quadTransform(w, h, quad) {
  const [[x0,y0],[x1,y1],[x2,y2],[x3,y3]] = quad;
  const dx1=x1-x2, dx2=x3-x2, dy1=y1-y2, dy2=y3-y2, sx=x0-x1+x2-x3, sy=y0-y1+y2-y3;
  const det=dx1*dy2-dx2*dy1, g=(sx*dy2-dx2*sy)/det, k=(dx1*sy-sx*dy1)/det;
  const a=x1-x0+g*x1, b=x3-x0+k*x3, d=y1-y0+g*y1, e=y3-y0+k*y3;
  return [a/w,d/w,0,g/w, b/h,e/h,0,k/h, 0,0,1,0, x0,y0,0,1];
}
export function applyQuadTransform(m, x, y) {
  const X=m[0]*x+m[4]*y+m[12], Y=m[1]*x+m[5]*y+m[13], W=m[3]*x+m[7]*y+m[15];
  return [X/W, Y/W];
}
