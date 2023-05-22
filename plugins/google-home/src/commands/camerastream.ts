import { RTCSignalingChannel, ScryptedDevice, ScryptedMimeTypes, VideoCamera } from "@scrypted/sdk";
import { executeResponse } from "../common";
import { commandHandlers } from "../handlers";

import sdk from "@scrypted/sdk";
const { mediaManager, endpointManager, systemManager } = sdk;

export const cameraTokens: { [token: string]: string } = {};

export function canAccess(token: string) {
    const id = cameraTokens[token];
    return systemManager.getDeviceById(id) as ScryptedDevice & RTCSignalingChannel;
}

commandHandlers['action.devices.commands.GetCameraStream'] = async (device: ScryptedDevice, execution) => {
    const ret = executeResponse(device);
    const { SupportedStreamProtocols } = execution.params;

    const cameraStreamAuthToken = `tok-${Math.round(Math.random() * 10000).toString(36)}`;
    cameraTokens[cameraStreamAuthToken] = device.id;

    if (SupportedStreamProtocols.length === 1 && SupportedStreamProtocols.includes('hls')) {
        ret.states = {
            cameraStreamAccessUrl: `https://scrypted.koush.com/endpoint/@scrypted/google-home/public/${cameraStreamAuthToken}.mp4`,
            cameraStreamProtocol: "hls",
            // cameraStreamAuthToken,
        };
    }
    else {
        const engineio = await endpointManager.getPublicLocalEndpoint() + 'engine.io/';
        const mo = await mediaManager.createMediaObject(Buffer.from(engineio), ScryptedMimeTypes.LocalUrl);
        const cameraStreamAccessUrl = await mediaManager.convertMediaObjectToUrl(mo, ScryptedMimeTypes.LocalUrl);

        ret.states = {
            cameraStreamAccessUrl,
            // cameraStreamReceiverAppId: "9E3714BD",
            cameraStreamReceiverAppId: "00F7C5DD",
            cameraStreamAuthToken,
        }
    }

    return ret;
}
