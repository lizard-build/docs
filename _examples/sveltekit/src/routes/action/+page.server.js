export const actions={default:async({request})=>({message:(await request.formData()).get('message')})};
