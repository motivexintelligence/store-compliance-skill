import { identifier } from '@kit.AdsKit';

@Entry
@Component
struct Index {
  aboutToAppear() {
    identifier.getOAID();
  }
  build() {
    Text('Coming soon')
  }
}
