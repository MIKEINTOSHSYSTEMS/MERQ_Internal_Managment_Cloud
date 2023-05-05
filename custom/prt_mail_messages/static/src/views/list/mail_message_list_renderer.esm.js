/** @odoo-module **/

import {ListRenderer} from "@web/views/list/list_renderer";

export class MailMessageUpdateListRenderer extends ListRenderer {
    getCellTitle(column, record) {
        const col = this.props.archInfo.fieldNodes.plain_body;
        if (column.name === "subject_display" && col) {
            return super.getCellTitle(col, record);
        }
        return super.getCellTitle(column, record);
    }
}
