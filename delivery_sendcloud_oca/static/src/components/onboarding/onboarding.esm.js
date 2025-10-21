import {Component, onWillStart} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class SendcloudOnboarding extends Component {
    static template = "sendcloud.Onboarding";
    static props = {};
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.steps = null;
        this.onboarding_state = null;
        onWillStart(this.onWillStart);
    }

    async onWillStart() {
        const onboarding_data = await this.orm.call(
            "onboarding.onboarding",
            "get_sendcloud_onboarding_data",
            [],
            {}
        );
        this.steps = onboarding_data.steps;
        this.onboarding_state = onboarding_data.onboarding_state;
    }

    async onboardingLinkClicked(step) {
        const action = await this.orm.call(
            "onboarding.onboarding.step",
            step.action,
            [],
            {}
        );
        this.action.doAction(action, {
            onClose: async () => {
                await this.onWillStart();
                this.render();
            },
        });
    }
}
