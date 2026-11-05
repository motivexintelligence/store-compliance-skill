import { UIAbility, abilityAccessCtrl } from '@kit.AbilityKit';

export default class EntryAbility extends UIAbility {
  onCreate(): void {
    UMConfigure.init(this.context);
    abilityAccessCtrl.createAtManager().requestPermissionsFromUser(this.context, ['ohos.permission.CAMERA']);
  }
}
